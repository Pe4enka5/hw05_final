import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from http import HTTPStatus
from ..models import Post, Group, Comment
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


User = get_user_model()
NUMBER_OF_NEW_ENTRIES = 1
NUMBER_OF_GUEST_USER_POSTS = 0
NUMBER_OF_NEW_COMMENTS = 1
NUMBER_OF_NEW_GUEST_COMMENTS = 0
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка создания нового поста в БД"""
        form_data = {'text': 'Новая запись в БД',
                     'group': self.group.id}
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        post = response.context.get('post')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), NUMBER_OF_NEW_ENTRIES)
        self.assertEqual(post.text, 'Новая запись в БД')
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)

    def test_post_edit(self):
        """Проверка обновления поста в БД"""
        group = Group.objects.create(title='Тестовая группа 2',
                                     slug='test-group 2',
                                     description='Тестовое описание 2'
                                     )
        post = Post.objects.create(text='Тестовый текст',
                                        author=self.user,
                                        group=group)
        form_data = {'text': 'Новая запись в БД 2',
                     'group': 'test-group 2'}
        response = self.authorized_client.post(reverse('posts:post_edit',
                                               kwargs={'post_id':
                                                       post.id}),
                                               data=form_data,
                                               follow=True)
        post = response.context.get('post')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post.text, 'Новая запись в БД 2')
        self.assertEqual(post.group, group)
        self.assertEqual(post.author, self.user)

    def test_client_post_create(self):
        """Проверка запрета создания поста не авторизованного пользователя"""
        form_data = {'text': 'Текст записанный в форму',
                     'group': self.group.id}
        response = self.guest_client.post(reverse('posts:post_create'),
                                          data=form_data,
                                          follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), NUMBER_OF_GUEST_USER_POSTS)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_creating_a_post_with_a_picture(self):
        """Проверка создания нового поста с картинкой в БД"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {'text': 'Новая запись в БД',
                     'group': self.group.id,
                     'image': uploaded}
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        post = response.context.get('post')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), NUMBER_OF_NEW_ENTRIES)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_new_comment(self):
        """Проверка создания нового комментария в БД"""
        post = Post.objects.create(text='Тестовый текст',
                                        author=self.user,
                                        group=self.group)
        form_data = {'post': post,
                     'author': self.user,
                     'text': 'Новый коммент'}
        response = self.authorized_client.post(reverse('posts:add_comment',
                                               kwargs={'post_id':
                                                       post.id}),
                                               data=form_data,
                                               follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), NUMBER_OF_NEW_COMMENTS)
        self.assertTrue(
            Comment.objects.filter(
                text='Новый коммент',
            ).exists()
        )

    def test_client_post_comment(self):
        """Проверка запрета создания комментария
        для авторизованного пользователя"""
        post = Post.objects.create(text='Тестовый текст',
                                        author=self.user,
                                        group=self.group)
        form_data = {'post': post,
                     'author': self.user,
                     'text': 'Новый коммент'}
        response = self.guest_client.post(reverse('posts:add_comment',
                                          kwargs={'post_id':
                                                  post.id}),
                                          data=form_data,
                                          follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), NUMBER_OF_NEW_GUEST_COMMENTS)
