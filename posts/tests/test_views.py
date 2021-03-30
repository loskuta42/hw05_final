import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostPagesTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(
            username='test_author'
        )
        cls.auth_author_client = Client()
        cls.auth_author_client.force_login(cls.author)
        cls.not_author = User.objects.create_user(
            username='test_not_author'
        )
        cls.authorized_not_author_client = Client()
        cls.authorized_not_author_client.force_login(cls.not_author)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author,
            image=cls.uploaded
        )
        cls.templ_names = {
            reverse('index'): 'index.html',
            reverse(
                'group',
                args=[cls.group.slug]
            ): 'group.html',
            reverse('new_post'): 'new.html',
            reverse('post_edit',
                    kwargs={
                        'username': cls.author.username,
                        'post_id': cls.post.pk
                    }
                    ): 'new.html',
            reverse('profile',
                    args=[cls.author.username]
                    ): 'profile.html',
            reverse('post',
                    kwargs={
                        'username': cls.author.username,
                        'post_id': cls.post.pk
                    }
                    ): 'post.html',
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        for reverse_name, template in PostPagesTest.templ_names.items():
            with self.subTest(template=template):
                response = PostPagesTest.auth_author_client.get(
                    reverse_name
                )
                self.assertTemplateUsed(response, template)

    def test_new_show_correct_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = PostPagesTest.auth_author_client.get(
            reverse('new_post')
        )
        response_title = response.context.get('title')
        response_button = response.context.get('button')
        for value, expected in PostPagesTest.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response_title, 'Новая запись')
        self.assertEqual(response_button, 'Создать новую запись')

    def test_index_page_list_is_1(self):
        """На страницу index передаётся ожидаемое количество объектов."""
        response = PostPagesTest.auth_author_client.get(reverse('index'))
        self.assertEqual(len(response.context.get(
            'page'
        ).object_list), 1)

    def test_group_page_list_is_1(self):
        """На страницу group передаётся ожидаемое количество объектов."""
        response = PostPagesTest.auth_author_client.get(
            reverse('group', args=[PostPagesTest.group.slug])
        )
        correct_post = response.context.get(
            'page'
        ).object_list[0]
        self.assertEqual(len(response.context.get('page').object_list), 1)
        self.assertEqual(correct_post, PostPagesTest.post)

    def post_test(self, response_post):
        post = PostPagesTest.post
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, PostPagesTest.author)
        self.assertEqual(post_group, PostPagesTest.group)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = PostPagesTest.guest_client.get(reverse('index'))
        response_post = response.context.get('page').object_list[0]
        self.post_test(response_post)

    def test_index_show_correct_profile(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = PostPagesTest.guest_client.get(
            reverse('profile', args=[PostPagesTest.author.username])
        )
        author = PostPagesTest.author
        response_author = response.context.get('author')
        response_count = response.context.get('count')
        response_post = response.context.get('page').object_list[0]
        self.post_test(response_post)
        self.assertEqual(author, response_author)
        self.assertEqual(1, response_count)

    def test_index_show_correct_post_view(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = PostPagesTest.guest_client.get(
            reverse(
                'post',
                kwargs={
                    'username': PostPagesTest.author.username,
                    'post_id': PostPagesTest.post.pk
                }
            )
        )
        author = PostPagesTest.author
        response_post = response.context.get('post')
        response_author = response.context.get('author')
        response_count = response.context.get('count')
        self.post_test(response_post)
        self.assertEqual(author, response_author)
        self.assertEqual(1, response_count)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = PostPagesTest.auth_author_client.get(
            reverse('post_edit',
                    kwargs={
                        'username': PostPagesTest.author.username,
                        'post_id': PostPagesTest.post.pk
                    }
                    )
        )
        response_title = response.context.get('title')
        response_button = response.context.get('button')
        for value, expected in PostPagesTest.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response_title, 'Редактировать запись')
        self.assertEqual(response_button, 'Сохранить запись')

    def test_group_slug_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = PostPagesTest.auth_author_client.get(
            reverse('group', args=[PostPagesTest.group.slug])
        )
        response_post = response.context.get('page').object_list[0]
        self.post_test(response_post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text=f'test_post{i}',
                group=cls.group,
                author=cls.author
            )

        cls.templates = {
            1: reverse('index'),
            2: reverse('group', args=[cls.group.slug]),
            3: reverse('profile', args=[cls.author.username])
        }

    def test_first_page_contains_ten_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на первую страницую."""
        for i in PaginatorViewsTest.templates.keys():
            with self.subTest(i=i):
                response = self.client.get(self.templates[i])
                self.assertEqual(len(response.context.get(
                    'page'
                ).object_list), 10)

    def test_second_page_contains_three_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на вторую страницую."""
        for i in PaginatorViewsTest.templates.keys():
            with self.subTest(i=i):
                response = self.client.get(self.templates[i], {'page': 2})
                self.assertEqual(len(response.context.get(
                    'page'
                ).object_list), 3)


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = CacheViewsTest.authorized_client.get(reverse('index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=CacheViewsTest.author,
        )
        response_old = CacheViewsTest.authorized_client.get(
            reverse('index')
        )
        old_posts = response_old.content
        self.assertEqual(
            old_posts,
            posts,
            'Не возвращает кэшированную страницу.'
        )
        cache.clear()
        response_new = CacheViewsTest.authorized_client.get(reverse('index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts, 'Нет сброса кэша.')


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(
            username='test_author'
        )
        cls.auth_author_client = Client()
        cls.auth_author_client.force_login(cls.author)

        cls.user_fol = User.objects.create_user(
            username='test_user_fol'
        )
        cls.authorized_user_fol_client = Client()
        cls.authorized_user_fol_client.force_login(
            cls.user_fol
        )

        cls.user_unfol = User.objects.create_user(
            username='test_user_unfol'
        )
        cls.authorized_user_unfol_client = Client()
        cls.authorized_user_unfol_client.force_login(
            cls.user_unfol
        )
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_follow(self):
        """Тест работы подписки на автора."""
        client = FollowViewsTest.authorized_user_unfol_client
        user = FollowViewsTest.user_unfol
        author = FollowViewsTest.author
        client.get(
            reverse(
                'profile_follow',
                args=[author.username]
            )
        )
        follower = Follow.objects.filter(
            user=user,
            author=author
        ).exists()
        self.assertTrue(
            follower,
            'Не работает подписка на автора'
        )

    def test_unfollow(self):
        """Тест работы отписки от автора."""
        client = FollowViewsTest.authorized_user_unfol_client
        user = FollowViewsTest.user_unfol
        author = FollowViewsTest.author
        client.get(
            reverse(
                'profile_unfollow',
                args=[author.username]
            ),

        )
        follower = Follow.objects.filter(
            user=user,
            author=author
        ).exists()
        self.assertFalse(
            follower,
            'Не работает отписка от автора'
        )

    def test_new_author_post_for_follower(self):
        client = FollowViewsTest.authorized_user_fol_client
        author = FollowViewsTest.author
        group = FollowViewsTest.group
        client.get(
            reverse(
                'profile_follow',
                args=[author.username]
            )
        )
        response_old = client.get(
            reverse('follow_index')
        )
        old_posts = response_old.context.get(
            'page'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page').object_list),
            1,
            'Не загружается правильное колличество старых постов'
        )
        self.assertIn(
            FollowViewsTest.post,
            old_posts,
            'Старый пост не верен'
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=group,
            author=author
        )
        cache.clear()
        response_new = client.get(
            reverse('follow_index')
        )
        new_posts = response_new.context.get(
            'page'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page').object_list),
            2,
            'Нету нового поста'
        )
        self.assertIn(
            new_post,
            new_posts,
            'Новый пост не верен'
        )

    def test_new_author_post_for_unfollower(self):
        client = FollowViewsTest.authorized_user_unfol_client
        author = FollowViewsTest.author
        group = FollowViewsTest.group
        response_old = client.get(
            reverse('follow_index')
        )
        old_posts = response_old.context.get(
            'page'
        ).object_list
        self.assertEqual(
            len(response_old.context.get('page').object_list),
            0,
            'Не загружается правильное колличество старых постов'
        )
        self.assertNotIn(
            FollowViewsTest.post,
            old_posts,
            'Старый пост не должен загружаться'
        )
        new_post = Post.objects.create(
            text='test_new_post',
            group=group,
            author=author
        )
        cache.clear()
        response_new = client.get(
            reverse('follow_index')
        )
        new_posts = response_new.context.get(
            'page'
        ).object_list
        self.assertEqual(
            len(response_new.context.get('page').object_list),
            0,
            'Новый пост не должен появляться'
        )
        self.assertNotIn(
            new_post,
            new_posts,
            'Новый пост не должен появляться'
        )


class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

        cls.auth_user = User.objects.create_user(
            username='test_auth_user'
        )
        cls.auth_auth_user_client = Client()
        cls.auth_auth_user_client.force_login(cls.auth_user)

        cls.author = User.objects.create_user(
            username='test_author'
        )
        cls.auth_author_client = Client()
        cls.auth_author_client.force_login(cls.author)

        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )

        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_add_comment_for_guest(self):
        response = CommentViewsTest.guest_client.get(
            reverse(
                'add_comment',
                kwargs={
                    'username': CommentViewsTest.author.username,
                    'post_id': CommentViewsTest.post.pk
                }
            )
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            ('Неавторизированный пользователь'
             ' не может оставлять комментарий')
        )

    def test_comment_for_auth_user(self):
        """Авторизированный пользователь может оставить комментарий"""
        client = CommentViewsTest.auth_auth_user_client
        author = CommentViewsTest.author
        post = CommentViewsTest.post
        response = client.get(
            reverse(
                'add_comment',
                kwargs={
                    'username': author.username,
                    'post_id': post.pk
                }
            )
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            ('Авторизированный пользователь'
             ' должен иметь возможность'
             ' оставлять комментарий')
        )
        comments_count = Comment.objects.filter(
            post=post.pk
        ).count()
        form_data = {
            'text': 'test_comment',
        }

        response = client.post(
            reverse('add_comment',
                    kwargs={
                        'username': author.username,
                        'post_id': post.pk
                    }
                    ),
            data=form_data,
            follow=True
        )
        comments = Post.objects.filter(
            id=post.pk
        ).values_list('comments', flat=True)
        self.assertRedirects(
            response,
            reverse(
                'post',
                kwargs={
                    'username': author.username,
                    'post_id': post.pk
                }
            )
        )
        self.assertEqual(
            comments.count(),
            comments_count + 1
        )
        self.assertTrue(
            Comment.objects.filter(
                post=post.pk,
                author=CommentViewsTest.auth_user.pk,
                text=form_data['text']
            ).exists()
        )
