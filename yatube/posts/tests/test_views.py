import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, override_settings, TestCase
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from http import HTTPStatus

from ..forms import PostForm
from ..models import Follow, Group, Post

User = get_user_model()
TEST_OF_POST = 13
POSTS_ON_THE_FIRST_PAGE = 10
POSTS_ON_THE_SECOND_PAGE = 4
NUMBER_OF_POSTS = 1
NUMBER_OF_PAGES = 0
NUMBER_OF_FOLLOW = 1
NUMBER_OF_FOLLOW_AFTER_UNFOLLOWING = 0
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=(
                b'\x47\x49\x46\x38\x39\x61\x02\x00'
                b'\x01\x00\x80\x00\x00\x00\x00\x00'
                b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                b'\x0A\x00\x3B'
            ),
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            pub_date=timezone.now(),
            image=cls.uploaded)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
            reverse('posts:post_create'):
                'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile, post_detail
        сформированы с правильным контекстом и картинкой."""
        pages = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user}),
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        )
        for page in pages:
            with self.subTest():
                response = self.authorized_client.get(page)
                post = response.context.get('post')
                self.assertEqual(post.author, self.user)
                self.assertEqual(post.text, 'Тестовый пост')
                self.assertEqual(post.group, self.group)
                self.assertEqual(post.pub_date, self.post.pub_date)
                self.assertEqual(post.image, self.post.image)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})))
        group = response.context['group']
        self.assertEqual(group.title, 'Тестовая группа')
        self.assertEqual(group.slug, 'test_group')
        self.assertEqual(group.description, 'Тестовое описание')

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:profile',
                    kwargs={'username': self.user})))
        author = response.context['author']
        self.assertEqual(author, self.user)

    def test_post_create_and_edit_page_show_correct_context(self):
        """Шаблон post_create и post_edit
        сформирован с правильным контекстом."""
        url_names = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        for url_name in url_names:
            with self.subTest(url_name=url_name):
                response = self.authorized_client.get(url_name)
                self.assertIn('is_edit', response.context)
                if url_name == 'post_edit':
                    self.assertIs(response.context['is_edit'], True)
                elif url_name == 'post_create':
                    self.assertIs(response.context['is_edit'], False)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)

    def test_other_group_does_not_have_the_post(self):
        """Пост не попал в группу, для которой не был предназначен"""
        group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_group2',
            description='Тестовое описание 2',
        )
        response = (self.authorized_client.get(reverse('posts:group_list',
                    kwargs={'slug': group.slug})))
        self.assertEqual(response.context['page_obj'].paginator.count,
                         NUMBER_OF_PAGES)

    def test_paginator(self):
        """Проверка. На 1 странице должно быть 10 постов,
        на 2 странице 4 поста"""
        object_list = []
        for number in range(TEST_OF_POST):
            object_list.append(Post(text=f'Тестовый текст №{number}',
                                    group=self.group,
                                    author=self.user))
        Post.objects.bulk_create(object_list)
        urls = ('posts:index', None),
        ('posts:profile', PostPagesTests.user),
        ('posts:group_list', PostPagesTests.group.slug)
        pages = (
            (1, POSTS_ON_THE_FIRST_PAGE),
            (2, POSTS_ON_THE_SECOND_PAGE)
        )
        for url_name, args in urls:
            for page, count in pages:
                with self.subTest(page=page):
                    response = (self.authorized_client.get(reverse(url_name,
                                args=args), {'page': page}))
                    self.assertEqual(len(response.context.get('page_obj')),
                                     count)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='Andrey')
        cls.author = User.objects.create_user(username='Pecheritsa')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_auth_user_can_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться и
        отписываться от автора"""
        form_data = {'user': self.user,
                     'author': self.author}
        response = self.authorized_client.post(reverse('posts:profile_follow',
                                               kwargs={'username':
                                                       self.author.username}),
                                               data=form_data,
                                               follow=True)
        self.assertEqual(Follow.objects.all().count(), NUMBER_OF_FOLLOW)
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username':
                                                       self.author.username}))
        self.authorized_client.post(reverse('posts:profile_unfollow',
                                            kwargs={'username':
                                                    self.author.username}),
                                    data=form_data,
                                    follow=True)
        self.assertEqual(Follow.objects.all().count(),
                         NUMBER_OF_FOLLOW_AFTER_UNFOLLOWING)

    def test_follower_see_or_not_new_post(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        post = Post.objects.create(author=self.author,
                                   text='Тестовый пост')
        Follow.objects.create(user=self.user,
                              author=self.author)
        respone_follow = self.authorized_client.get(reverse(
                                                    'posts:follow_index'))
        posts_follow = respone_follow.context['page_obj']
        self.assertIn(post, posts_follow)
        respone_no_follower = self.authorized_client2.get(reverse(
                                                          'posts:follow_index')
                                                          )
        posts_no_follow = respone_no_follower.context['page_obj']
        self.assertNotIn(post, posts_no_follow)

    def test_cache_index_page(self):
        """ Проверка кэша страницы"""
        old_content = self.authorized_client.get('/').content
        Post.objects.all().delete()
        new_content = self.authorized_client.get('/').content
        self.assertEqual(old_content, new_content)
        cache.clear()
        clear_content = self.authorized_client.get('/').content
        self.assertNotEqual(old_content, clear_content)
