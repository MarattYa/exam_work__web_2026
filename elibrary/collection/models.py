from django.db import models
from django.contrib.auth.models import User
from books.models import Book

class Collection(models.Model):

    title = models.CharField(
        max_length=255
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    books = models.ManyToManyField(
        Book,
        blank=True
    )

    def __str__(self):
        return self.title