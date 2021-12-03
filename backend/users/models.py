from django.contrib.auth.models import AbstractUser
from django.db import models


class UserCustom(AbstractUser):
    first_name = models.CharField(
        'first name',
        max_length=30,
    )
    last_name = models.CharField(
        'last name',
        max_length=150,
    )
    email = models.EmailField(
        'email address',
        unique=True,
    )

    class Meta:
        app_label = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'