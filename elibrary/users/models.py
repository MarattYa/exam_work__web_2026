from django.db import models
from django.contrib.auth.models import User

class Role(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE
    )

    middle_name = models.CharField(
        max_length=100,
        blank=True
    )
    def set_profile(self, user, role, middle_name=''):
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.middle_name = middle_name
        profile.role = role
        profile.save()