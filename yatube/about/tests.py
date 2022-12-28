from django.test import Client, TestCase
from http import HTTPStatus


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_static_pages_url_for_all_users(self):
        """Проверка доступности адресов about/"""
        pages = ('/about/author/',
                 '/about/tech/')
        for page in pages:
            response = self.guest_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_static_pages_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон about/."""
        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'}
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
