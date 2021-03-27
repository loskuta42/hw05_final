import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.author = User.objects.create_user(username='testuser')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.auth_user = User.objects.create_user(
            username='test_auth_user'
        )
        cls.auth_user_client = Client()
        cls.auth_user_client.force_login(
            cls.auth_user
        )
        cls.small_gif_old1 = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.small_gif_old2 = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.small_gif_new = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded_old1 = SimpleUploadedFile(
            name='small_old1.gif',
            content=cls.small_gif_old1,
            content_type='image/gif'
        )
        cls.uploaded_old2 = SimpleUploadedFile(
            name='small_old2.gif',
            content=cls.small_gif_old2,
            content_type='image/gif'
        )
        cls.uploaded_new = SimpleUploadedFile(
            name='small_new.gif',
            content=cls.small_gif_new,
            content_type='image/gif'
        )
        cls.group_old = Group.objects.create(
            title='test_group_old',
            slug='test-slug-old',
            description='test_description'
        )
        cls.group_new = Group.objects.create(
            title='test_group_new',
            slug='test-slug-new',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group_old,
            author=cls.author,
            image=cls.uploaded_old1
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Проверка формы создания нового поста."""
        posts_count = Post.objects.count()
        group_field = PostFormTests.group_old.id
        form_data = {
            'text': 'test_new_post',
            'group': group_field,
            'image': PostFormTests.uploaded_old2
        }

        response = PostFormTests.author_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group_old.id,
                text='test_new_post',
                image='posts/small_old2.gif',
            ).exists()
        )

    def test_edit_post(self):
        """Проверка формы редактирования поста и изменение
        его в базе данных."""
        group_field_new = PostFormTests.group_new.id
        form_data = {
            'text': 'test_edit_post',
            'group': group_field_new,
            'image': PostFormTests.uploaded_new
        }
        response = PostFormTests.author_client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': PostFormTests.author.username,
                    'post_id': PostFormTests.post.pk
                }

            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'post',
                kwargs={
                    'username': PostFormTests.author.username,
                    'post_id': PostFormTests.post.pk
                }
            )
        )
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group_new.id,
                text='test_edit_post',
                image='posts/small_new.gif'
            ).exists()
        )
        self.assertFalse(
            Post.objects.filter(
                group=PostFormTests.group_old.id,
                text='test_post',
                image='posts/small_old1.gif'
            ).exists()
        )

    def test_create_comment(self):
        """Проверка формы создания нового комментария."""
        comments_count = Comment.objects.filter(
            post=PostFormTests.post.pk
        ).count()
        print(f'comments_count: {comments_count}')
        form_data = {
            'text': 'test_comment',
        }

        response = PostFormTests.auth_user_client.post(
            reverse('add_comment',
                    kwargs={
                        'username': PostFormTests.author.username,
                        'post_id': PostFormTests.post.pk
                    }
                    ),
            data=form_data,
            follow=True
        )
        comments = Post.objects.filter(
            id=PostFormTests.post.pk
        ).values_list('comments', flat=True)
        print(f'comments_count: {comments_count}')
        self.assertRedirects(
            response,
            reverse(
                'post',
                kwargs={
                    'username': PostFormTests.author.username,
                    'post_id': PostFormTests.post.pk
                }
            )
        )
        self.assertEqual(
            comments.count(),
            comments_count + 1
        )
        self.assertTrue(
            Comment.objects.filter(
                post=PostFormTests.post.pk,
                author=PostFormTests.auth_user.pk,
                text=form_data['text']
            ).exists()
        )
