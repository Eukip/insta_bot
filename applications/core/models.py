from django.db import models

from applications.core import constants


class Account(models.Model):
    social_media = models.IntegerField(
        'Социальная сеть',
        choices=constants.SOCIAL_MEDIA_CHOICES,
        default=constants.INSTAGRAM,
    )
    username = models.CharField('Логин', max_length=100)
    password = models.CharField('Пароль', max_length=100)

    class Meta:
        verbose_name = 'Аккаунт'
        verbose_name_plural = 'Аккаунты'
        ordering = ['username']
    
    def __str__(self):
        return self.username


class PublicPage(models.Model):
    social_media = models.IntegerField(
        'Социальная сеть',
        choices=constants.SOCIAL_MEDIA_CHOICES,
        default=constants.INSTAGRAM,
    )
    name = models.CharField('Название', max_length=100)
    url = models.URLField('Ссылка', max_length=500)

    class Meta:
        verbose_name = 'Публичная страница'
        verbose_name_plural = 'Публичные страницы'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Comment(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        verbose_name='Аккаунт',
        related_name='comments',
    )
    text = models.TextField('Текст')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-id']

    def __str__(self):
        return f'#{self.id}'


class Post(models.Model):
    social_media = models.IntegerField(
        'Социальная сеть',
        choices=constants.SOCIAL_MEDIA_CHOICES,
        default=constants.INSTAGRAM,
    )
    public_page = models.ForeignKey(
        PublicPage,
        verbose_name='Публичная страница',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    url = models.URLField('Ссылка', max_length=1000)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    added_to_gs = models.BooleanField('Статус добавления в Google таблицы', default=False)

    class Meta:
        verbose_name = 'Публикация'
        verbose_name_plural = 'Публикации'
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.id}'

