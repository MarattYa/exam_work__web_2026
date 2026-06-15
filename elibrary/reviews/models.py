from django.db import models
from django.contrib.auth.models import User
from books.models import Book

class Review(models.Model):

    SCORE_CHOICES = (
        (5, 'Отлично'),
        (4, 'Хорошо'),
        (3, 'Удовлетворительно'),
        (2, 'Неудовлетворительно'),
        (1, 'Плохо'),
        (0, 'Ужасно'),
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    score = models.IntegerField(
        choices=SCORE_CHOICES
    )

    text = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('book', 'user')