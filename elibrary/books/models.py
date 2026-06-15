from django.db import models

class Genre(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=255)

    description = models.TextField()

    year = models.IntegerField()

    publisher = models.CharField(max_length=255)

    author = models.CharField(max_length=255)

    pages = models.IntegerField()

    genres = models.ManyToManyField(
        Genre
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title

class Cover(models.Model):
    book = models.OneToOneField(
        Book,
        on_delete=models.CASCADE,
        related_name='cover'
    )

    image = models.ImageField(
        upload_to='covers/'
    )

    file_name = models.CharField(
        max_length=255
    )

    mime_type = models.CharField(
        max_length=100
    )

    md5_hash = models.CharField(
        max_length=32
    )

    def __str__(self):
        return self.file_name