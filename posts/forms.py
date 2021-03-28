from django.contrib.auth import get_user_model
from django.forms import ModelForm

from .models import Comment, Post

User = get_user_model()


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст записи',
            'group': 'Группа',
            'image': 'Изображение'
        }
        help_texts = {
            'text': 'Напишите сюда текст вашей записи.',
            'group': 'Группа, к которой отнести запись(необязательно).',
            'image': 'Прикрепите изображение'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст комментария.'
        }
        help_texts = {
            'text': 'Напишите сюда текст комментария.'
        }
