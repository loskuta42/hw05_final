import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class PostPagesTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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
            reverse('new_post'): 'posts/new.html',
            reverse('post_edit',
                    kwargs={
                        'username': cls.author.username,
                        'post_id': cls.post.pk
                    }
                    ): 'posts/new.html',
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

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = PostPagesTest.guest_client.get(reverse('index'))
        post = PostPagesTest.post
        response_post = response.context.get('page').object_list[0]
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, PostPagesTest.author)
        self.assertEqual(post_group, PostPagesTest.group)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)

    def test_index_show_correct_profile(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = PostPagesTest.guest_client.get(
            reverse('profile', args=[PostPagesTest.author.username])
        )
        post = PostPagesTest.post
        author = PostPagesTest.author
        response_author = response.context.get('author')
        response_count = response.context.get('count')
        response_post = response.context.get('page').object_list[0]
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, author)
        self.assertEqual(post_group, PostPagesTest.group)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)
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
        post = PostPagesTest.post
        author = PostPagesTest.author
        response_post = response.context.get('post')
        response_author = response.context.get('author')
        response_count = response.context.get('count')
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, author)
        self.assertEqual(post_group, PostPagesTest.group)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)
        self.assertEqual(post, response_post)
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
        post = PostPagesTest.post
        response_post = response.context.get('page').object_list[0]
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, PostPagesTest.author)
        self.assertEqual(post_group, PostPagesTest.group)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)

    def test_about_author_use_correct_view(self):
        """Шаблон author использует корректный view."""
        response = PostPagesTest.guest_client.get(
            reverse('about:author')
        )
        response_author = response.context.get('author')
        response_github = response.context.get('github')
        self.assertEqual(
            response_author,
            'Автор проекта - Алексей Лобарев.'
        )
        self.assertEqual(
            response_github,
            '<a href="https://github.com/loskuta42/">'
            'Ссылка на github</a>'
        )

    def test_about_tech_use_correct_view(self):
        """Шаблон tech использует корректный view."""
        response = PostPagesTest.guest_client.get(
            reverse('about:tech')
        )
        response_pycharm = response.context.get('pycharm')
        response_tech = response.context.get('tech')
        self.assertEqual(
            response_pycharm,
            'Сайт написан при использовании Pycharm.'
        )
        self.assertEqual(
            response_tech,
            'А так же модели, формы, декораторы и многое другое'
        )


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
                response = self.client.get(self.templates[i] + '?page=2')
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
        response_old = CacheViewsTest.authorized_client.get(reverse('index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts, 'Не возвращает кэшированную страницу.')
        cache.clear()
        response_new = CacheViewsTest.authorized_client.get(reverse('index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts, 'Нет сброса кэша.')
