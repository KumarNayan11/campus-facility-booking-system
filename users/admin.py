from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Inline panel shown inside the User admin page.
    Lets admins set the role without leaving the User form.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('role',)


class UserAdmin(BaseUserAdmin):
    """
    Extends Django's built-in UserAdmin to include the profile inline.
    Adds 'role' column to the user list.
    """
    inlines = (UserProfileInline,)
    list_display  = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')
    list_filter   = ('is_staff', 'is_superuser', 'profile__role')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    @admin.display(description='Role')
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return '—'


# Re-register User with the extended admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
