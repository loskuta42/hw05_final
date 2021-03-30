from http import HTTPStatus

from django.test import Client, TestCase


class AboutUrlsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_about_author(self):
        """Страница /about/author/ доступна любому пользователю."""
        response = AboutUrlsTest.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_tech(self):
        """Страница /about/author/ доступна любому пользователю."""
        response = AboutUrlsTest.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404(self):
        """При запросе несуществующей страницы сервер возвращает код 404."""
        response = AboutUrlsTest.guest_client.get('/about/тест/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
