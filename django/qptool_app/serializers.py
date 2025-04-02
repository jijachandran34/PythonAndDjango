from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class TagValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "key", "value"] 

class QuestionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionType
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'
        
class QuestionListSerializer(serializers.ModelSerializer):
    # Retrieve qtype_id instead of ID
    question_type = serializers.SlugRelatedField(
        queryset=QuestionType.objects.all(),
        slug_field='qtype_id'  
    )
    class Meta:
        model = Question
        fields = '__all__'


class QuestionDetailSerializer(serializers.ModelSerializer):
    question_type = QuestionTypeSerializer()
    tags = TagValueSerializer(many = True)
    class Meta:
        model = Question
        fields = "__all__"  

class QuestionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionGroup
        fields = '__all__'

class QuestionGroupOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionGroupOrder
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
    
    # to retrieve the details of item getting reviewed
    def get_resource_details(self, obj):
        serializer_map = {
            Question: QuestionSerializer,
            QuestionGroup: QuestionGroupSerializer,
        }
        serializer_class = serializer_map.get(type(obj.resource))
        if serializer_class:
            return serializer_class(obj.resource).data
        return None

class ReviewStatusUpdateSerializer(serializers.ModelSerializer):
    new_status = serializers.ChoiceField(choices=Review.STATUS_CHOICES)
    class Meta:
        model = ReviewStatusUpdate
        fields = '__all__'
        read_only_fields = ['old_status']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    # password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email']
    
    def create(self, validated_data):
        # Use create_user to ensure the password is hashed
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        return user

class AssetSerializer(serializers.ModelSerializer): 
    class Meta:
        model = AssetModel
        fields = ["id", "filename", "uploaded_at", "resource"]
