from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Department(models.Model):
    """
    An organizational unit (department / school / centre) in the campus.

    Facilities and user profiles can optionally be linked to a department,
    enabling future department-scoped administration.
    """

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Short identifier, e.g. "CS", "MECH", "ADMIN".',
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return f'{self.name} ({self.code})'


class UserProfile(models.Model):
    """
    Extends Django's built-in User with a role field and an optional department.

    The role field continues to drive broad app access, while facility-manager
    permissions are derived from the facilities assigned to the user.
    """

    ROLE_CHOICES = [
        ('user', 'User'),
        ('dept_admin', 'Department Admin'),
        ('sys_admin', 'System Admin'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        help_text='The department this user belongs to.',
    )

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

    def is_user(self):
        return self.role == 'user'

    def is_sys_admin(self):
        return self.role == 'sys_admin'

    def is_dept_admin(self):
        return self.role == 'dept_admin'

    def is_facility_manager(self):
        return self.is_sys_admin() or self.is_dept_admin() or self.user.managed_facilities.exists()

    def can_view_analytics(self):
        return self.is_facility_manager() or self.is_dept_admin()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile whenever a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Keep the profile in sync when the User is saved."""
    instance.profile.save()
