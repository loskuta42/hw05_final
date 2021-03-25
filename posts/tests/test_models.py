from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост' * 2,
            group=cls.group,
            author=User.objects.get(username='testuser')
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.user.delete()

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'group': 'Группа'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Напишите текст вашей записи.',
            'group': 'Группа, к которой относится запись.',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_object_name_is_title_fild(self):
        """В поле __str__  объектов post и group записано значение
         поля post.text[:15] и group.title"""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_object_post = post.text[:15]
        expected_object_group = group.title
        self.assertEqual(expected_object_group, str(group))
        self.assertEqual(expected_object_post, str(post))
