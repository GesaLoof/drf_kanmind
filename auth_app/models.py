from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """Extend the built-in User with a display name."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    fullname = models.CharField(max_length=100)

    def __str__(self):
        """Return the profile's full name."""
        return self.fullname
