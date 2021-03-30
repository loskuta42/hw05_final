from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AboutViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.auth_user = User.objects.create_user(
            username='test_auth_user'
        )
        cls.auth_user_client = Client()
        cls.auth_user_client.force_login(cls.auth_user)

        cls.templ_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }

    def test_about_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        for reverse_name, template in AboutViewsTest.templ_names.items():
            with self.subTest(template=template):
                response = AboutViewsTest.auth_user_client.get(
                    reverse_name
                )
                self.assertTemplateUsed(response, template)

    def test_about_author_use_correct_view(self):
        """Шаблон author использует корректный view."""
        response = AboutViewsTest.guest_client.get(
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
        response = AboutViewsTest.guest_client.get(
            reverse('about:tech')
        )
        response_pycharm = response.context.get('pycharm')
        response_tech = response.context.get('tech')
        self.assertEqual(
            response_pycharm,
            'Сайт написан при использовании python и Django.'
        )
        self.assertEqual(
            response_tech,
            'А так же модели, формы, декораторы и многое другое'
        )
