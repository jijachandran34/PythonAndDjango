from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth.models import Group, Permission


# class User(AbstractUser):
#     email = models.EmailField(unique=True)
class User(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",  # Change the related_name to avoid clashes
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions_set",  # Change the related_name
        blank=True
    )

class Base(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name="%(class)s_updated"
    )

    class Meta:
        abstract = True 
    
class Tag(Base):
    key = models.CharField(max_length=255,blank=False, null=False)
    value = models.CharField(max_length=255,blank=False,null=False)
    
    class Meta:
        unique_together = ('key', 'value')
        constraints = [models.UniqueConstraint(fields=['key', 'value'], name='unique_key_value')]

    def __str__(self):
        return f"{self.key}: {self.value}"

class QuestionType(Base):
    qtype_id = models.CharField(max_length=50, unique=True)# MCQ,MSQ etc
    description = models.TextField()
    how_to = models.URLField(blank=True, null=True) # help link
    
    class Meta:
        verbose_name = "Question Type"
        verbose_name_plural = "Question Types"

    def __str__(self):
        return f"{self.qtype_id.upper()} : {self.description}"

class Resource(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('inactive', 'Inactive'),
        ('closed', 'Closed')
    ]
    
    uid = models.CharField(max_length=255)
    revision_id = models.IntegerField(default=1)
    copied_from = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    tags = models.ManyToManyField(Tag, blank=True, related_name="%(class)s_tags")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        default=1, 
        related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name="%(class)s_updated"
    )
    
    def __str__(self):
        return f"{self.id} - {self.uid.upper()} : {self.revision_id} : {self.status}"
    
    class Meta:
        constraints = [models.UniqueConstraint(fields=['uid', 'revision_id'], name='unique_uid_revision')]
        managed = False
    
class Question(Resource):
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE)
    content = models.JSONField()  

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return f"{self.id} - {self.uid.upper()} : {self.revision_id}" 

class QuestionGroup(Resource):
    questions = models.ManyToManyField(Question, through='QuestionGroupOrder')
    description = models.TextField()    

    class Meta:
        verbose_name = "Question Group"
        verbose_name_plural = "Question Groups" 

    def __str__(self):
        return f"{self.id} - {self.uid.upper()}: {self.revision_id}"

class QuestionGroupOrder(models.Model):
    question_group = models.ForeignKey(QuestionGroup, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['order']
        unique_together = ('question_group', 'question')

class Review(Base):
    STATUS_CHOICES = [
        ('for_review', 'For Review'),
        ('in_progress', 'In Progress'),
        ('need_changes', 'Need Changes'),
        ('review_complete', 'Review Complete')
    ]
    
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='for_review')
    reviewer = models.ForeignKey(User, related_name='reviews_given', on_delete=models.CASCADE)
    reviewee = models.ForeignKey(User, related_name='reviews_received', on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True, related_name ='reviews')

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    def __str__(self):
        return f"Review of  - {self.id} - {self.resource.uid.upper()} : {self.resource.revision_id}"

class ReviewStatusUpdate(Base):
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=255, null=True, blank=True)  # Allow null values
    new_status = models.CharField(max_length=20, choices=Review.STATUS_CHOICES)
    
    class Meta:
        verbose_name = "Update Review Status"
        verbose_name_plural = "Update Review Status"

class Comment(Base):
    text = models.TextField()
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    resolved = models.BooleanField(default=False)
    resolved_on = models.DateTimeField(null=True, blank=True)
    replied_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    position = models.JSONField(null=True, blank=True)
    
class AssetModel(models.Model):  
    filename = models.CharField(max_length=255)
    file_data = models.BinaryField()  
    uploaded_at = models.DateTimeField(auto_now_add=True)
    content_type = models.CharField(max_length=100) 
    resource = models.ForeignKey("Resource", on_delete=models.CASCADE, related_name="assets")
