from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from ..models import Post, Group
from django.core.cache import cache

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_not_found_all_users(self):
        """Страница 404 доступна """
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_for_all_users(self):
        """Страницы доступны любому пользователю."""
        pages = ('/',
                 f'/group/{self.group.slug}/',
                 f'/profile/{self.user}/',
                 f'/posts/{self.post.id}/')
        for page in pages:
            response = self.guest_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authenticated_author_can_access_private_urls(self):
        """Страница /create/, posts/<int:post_id>/edit/ и
        posts/<int:post_id>/comment/ доступны авторизованному пользователю."""
        pages = ('/create/',
                 f'/posts/{self.post.id}/edit/')
        for page in pages:
            response = self.authorized_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ и posts/<int:post_id>/edit/
        перенаправит анонимного пользователя на страницу логина."""
        redirect_url = '/auth/login/?next='
        pages = {'/create/': f'{redirect_url}/create/',
                 f'/posts/{self.post.id}/edit/':
                 f'{redirect_url}/posts/{self.post.id}/edit/'
                 }
        for page, value in pages.items():
            response = self.guest_client.get(page, follow=True)
            self.assertRedirects(response, value)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_non_author_cannot_edit_post(self):
        """Страница по адресу post_detail
        недоступна для других пользователей, кроме автора"""
        self.user = User.objects.create_user(username='Andrey')
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост 2')
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_cache_index_page(self):
        """ Проверка кэша страницы"""
        old_content = self.authorized_client.get('/').content
        Post.objects.all().delete()
        new_content = self.authorized_client.get('/').content
        self.assertEqual(old_content, new_content)
        cache.clear()
        clear_content = self.authorized_client.get('/').content
        self.assertNotEqual(old_content, clear_content)
