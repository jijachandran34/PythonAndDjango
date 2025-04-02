from rest_framework import status,generics,viewsets,mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.authentication import BasicAuthentication
from django.utils import timezone
from rest_framework.permissions import AllowAny

from django.db.models import Max
from rest_framework.parsers import MultiPartParser
from django.http import HttpResponse
import mimetypes


from .models import *
from .serializers import *

class ReadWriteModelViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,  
    viewsets.GenericViewSet
):
    """
    A custom viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, and `list()` actions.
    (Destroy is removed)
    """
    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "DELETE method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class TagViewSet(mixins.CreateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,  
                 viewsets.GenericViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user) 

class QuestionTypeViewSet(viewsets.ModelViewSet):
    queryset = QuestionType.objects.all()
    serializer_class = QuestionTypeSerializer

    """Automatically set `created_by` or `updated_by`  when a new record is created."""
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
class QuestionViewSet(ReadWriteModelViewSet):
    queryset = Question.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """To Return different serializer based on action"""

        if self.action == "list":
            return QuestionListSerializer 
        elif self.action == "create" or self.action == "update":
            return QuestionSerializer 
        return QuestionDetailSerializer

    def get_object(self):
        if self.request.method == 'PUT':
            return None
        uid = self.kwargs.get("uid", None)
        revision_id = self.kwargs.get("revision_id", None)
        if not uid or not revision_id:
            raise generics.Http404("Question not found.")
        return generics.get_object_or_404(self.queryset, uid=uid, revision_id=revision_id)
            
    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def update(self, request, *args, **kwargs):
        request.data["revision_id"] = request.data["revision_id"] + 1 # to save a new record on update
        request.data["updated_by"] = request.user.id  
        request_id = request.data.pop("id")
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class QuestionGroupViewSet(QuestionViewSet):
    queryset = QuestionGroup.objects.all()
    serializer_class = QuestionGroupSerializer
    def create(self, request, *args, **kwargs):
        data = request.data
        questions_data = data.pop('questions', [])

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        question_group = serializer.save(created_by=request.user)
        if questions_data:
            question_group_orders = [
            QuestionGroupOrder(
                question_group=question_group,
                question=Question.objects.get(id=question_id),
                order=order
            )
            for order, question_id in enumerate(questions_data, start=1)
            ]
            QuestionGroupOrder.objects.bulk_create(question_group_orders)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class QuestionGroupOrderViewSet(ReadWriteModelViewSet):
    queryset = QuestionGroupOrder.objects.all()
    serializer_class = QuestionGroupOrderSerializer

class ReviewViewSet(ReadWriteModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    review_status_update = ReviewStatusUpdate()
    
    def update(self, request, *args, **kwargs):
        review = generics.get_object_or_404(Review, pk=kwargs.get('pk'))
        old_status = review.status
        serializer = self.get_serializer(review, data=request.data, partial=True)
        
        if serializer.is_valid():
            response = serializer.save(updated_by=self.request.user)
            new_status = response.status
            ReviewStatusUpdate.objects.create(
            review=review,
            old_status=old_status,
            new_status=new_status
            )
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(created_by=self.request.user)

        """ To Create the first entry in the ReviewStatusUpdate table """

        ReviewStatusUpdate.objects.create(
            review=review,
            old_status=None,
            new_status=review.status
        )
        serializer.save(created_by=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ReviewStatusUpdateViewSet(ReadWriteModelViewSet):
    queryset = ReviewStatusUpdate.objects.all()
    serializer_class = ReviewStatusUpdateSerializer

class CommentViewSet(ReadWriteModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        
        review_id = request.data.get("review")
        review = Review.objects.filter(id=review_id).select_related('resource').first()
        resource = review.resource

        """ To allow commenting only on the latest revision of resource"""

        if hasattr(resource, "question"):
            latest_revision = Question.objects.filter(uid=resource.uid).aggregate(Max('revision_id'))['revision_id__max']
        elif hasattr(resource,"questiongroup"):
            latest_revision = QuestionGroup.objects.filter(uid=resource.uid).aggregate(Max('revision_id'))['revision_id__max']
        else:
            latest_revision =None

        if resource.revision_id != latest_revision:
            return Response({"detail": "The revision of the resource is not latest ."}, status.HTTP_400_BAD_REQUEST)
        serializer.save(created_by=request.user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """ To update the resolved_on date to now on PUT with resolved = true """

        if request.data["resolved"] == True:
            request.data["resolved_on"] = timezone.now()
            request.data["updated_by"]=request.user.id
            return super().update(request, *args, **kwargs)
        else:
            return Response({"detail": "Only partial update of the resolved field is allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        if request.data["resolved"] == True:
            request.data["resolved_on"] = timezone.now()
            request.data["updated_by"]=request.user.id
            return super().update(request, *args, **kwargs)
        else:
            return Response({"detail": "Only partial updates of the resolved field is allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class AssetViewSet(viewsets.ModelViewSet):  # Renamed from ImageViewSet
    queryset = AssetModel.objects.all()
    serializer_class = AssetSerializer
    parser_classes = [MultiPartParser]  

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES["file"]
        binary_data = file_obj.read()

        resource_id = request.data.get("resource_id")  

        asset = AssetModel.objects.create(
            filename=file_obj.name, 
            file_data=binary_data,
            resource_id=resource_id  # Link asset to a resource
        )

        return Response({"message": "File uploaded successfully", "file_id": asset.id})

    def retrieve(self, request, pk=None):
        """ Serve the file as binary content with proper MIME type """
        asset = self.get_object()
        file_type = mimetypes.guess_type(asset.filename)[0] or "application/octet-stream"
        return HttpResponse(asset.file_data, content_type=file_type)
