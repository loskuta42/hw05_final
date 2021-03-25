from django.contrib.auth import get_user_model
from django.forms import ModelForm

from .models import Post, Comment

User = get_user_model()


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

