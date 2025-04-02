from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'tags', TagViewSet)
router.register(r'question-types', QuestionTypeViewSet)
router.register(r'questions', QuestionViewSet)

router.register(r'question-groups', QuestionGroupViewSet)
router.register(r'question-group-orders', QuestionGroupOrderViewSet)

router.register(r'reviews', ReviewViewSet)
router.register(r'review-status-updates', ReviewStatusUpdateViewSet)
router.register(r'comments', CommentViewSet)

router.register(r'users', UserViewSet)

router.register(r"assets", AssetViewSet)

urlpatterns = [
    path('', include(router.urls)),

    path('questions/<str:uid>/<int:revision_id>/', QuestionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='question-detail-by-uid-revision'),
    path('question-groups/<str:uid>/<int:revision_id>/', QuestionGroupViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='question-group-detail-by-uid-revision'),
    path('reviews/<int:pk>/', ReviewViewSet.as_view({'post': 'update_status'}), name='review-update-status'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

