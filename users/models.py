from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extends Django's built-in User with a role field.
    Uses OneToOneField so Django auth (sessions, passwords, permissions) is untouched.
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student',
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def is_admin(self):
        return self.role == 'admin'

    def is_student(self):
        return self.role == 'student'


# ── Signals ─────────────────────────────────────────────────────────────────

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile whenever a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Keep the profile in sync when the User is saved."""
    instance.profile.save()
