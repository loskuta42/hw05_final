from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(
            username='test_author'
        )
        cls.authorized_author_client = Client()
        cls.authorized_author_client.force_login(cls.author)
        cls.not_author = User.objects.create_user(
            username='test_not_author'
        )
        cls.authorized_not_author_client = Client()
        cls.authorized_not_author_client.force_login(cls.not_author)
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
        cls.templates_url_names = {
            '/': 'index.html',
            '/follow/': 'follow.html',
            f'/group/{cls.group.slug}/': 'group.html',
            '/new/': 'posts/new.html',
            (f'/{cls.author.username}/'
             f'{cls.post.pk}/edit/'): 'posts/new.html',
            f'/{cls.author.username}/': 'profile.html',
            f'/{cls.author.username}/{cls.post.pk}/': 'post.html'
        }

    def test_index(self):
        """Страница / доступна любому пользователю."""
        response = PostURLTests.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_follow(self):
        """Страница follow доступна авторизированному
         пользователю пользователю."""
        response = PostURLTests.authorized_not_author_client.get(
            '/follow/'
        )
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        """Страница /<username>/ доступна любому пользователю."""
        response = PostURLTests.guest_client.get(
            f'/{PostURLTests.author.username}/'
        )
        self.assertEqual(response.status_code, 200)

    def test_profile_post(self):
        """Страница /<username>/<post_id>/ доступна любому пользователю."""
        response = PostURLTests.guest_client.get(
            f'/{PostURLTests.author.username}/{PostURLTests.post.pk}/'
        )
        self.assertEqual(response.status_code, 200)

    def test_profile_post_edit_not_auth(self):
        """Страница /<username>/<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = PostURLTests.guest_client.get(
            (f'/{PostURLTests.author.username}/'
             f'{PostURLTests.post.pk}/edit/'),
            follow=True
        )
        self.assertRedirects(
            response,
            (f'/auth/login/?next=/'
             f'{PostURLTests.author.username}/'
             f'{PostURLTests.post.pk}/edit/')
        )

    def test_profile_post_edit_auth_not_author(self):
        """Страница /<username>/<post_id>/edit/ перенаправит
         авторизированного пользователя(не автора поста) на страницу поста.
        """
        response = PostURLTests.authorized_not_author_client.get(
            (f'/{PostURLTests.author.username}/'
             f'{PostURLTests.post.pk}/edit/'),
            follow=True
        )
        self.assertRedirects(
            response, (f'/{PostURLTests.author.username}/'
                       f'{PostURLTests.post.pk}/'))

    def test_profile_post_edit_auth_author(self):
        """Страница /<username>/<post_id>/edit/ доступна
         автору поста.
        """
        response = PostURLTests.authorized_author_client.get(
            (f'/{PostURLTests.author.username}/'
             f'{PostURLTests.post.pk}/edit/')
        )
        self.assertEqual(response.status_code, 200)

    def test_group_slug(self):
        """Страница /group/test-slug/ доступна любому пользователю."""
        response = PostURLTests.guest_client.get(
            f'/group/{PostURLTests.group.slug}/'
        )
        self.assertEqual(response.status_code, 200)

    def test_new(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = PostURLTests.authorized_author_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_about_author(self):
        """Страница /about/author/ доступна любому пользователю."""
        response = PostURLTests.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_about_tech(self):
        """Страница /about/author/ доступна любому пользователю."""
        response = PostURLTests.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)

    def test_404(self):
        """При запросе несуществующей страницы сервер возвращает код 404."""
        response = PostURLTests.guest_client.get('/about/тест/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in PostURLTests.templates_url_names.items():
            with self.subTest(url=url):
                response = PostURLTests.authorized_author_client.get(url)
                self.assertTemplateUsed(response, template)
