from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class RegisterForm(UserCreationForm):
    """
    Extends Django's built-in UserCreationForm with email + role selection.
    Role determines which Django Group the user is placed in.
    """
    email = forms.EmailField(required=True)
    role  = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        initial='student',
        help_text='Admins can manage facilities; Students can book them.',
    )

    class Meta:
        model  = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Profile was already auto-created by the signal; just update the role
            user.profile.role = self.cleaned_data['role']
            user.profile.save()
            # Add user to the matching Django Group for permission-based access
            from django.contrib.auth.models import Group
            group_name = 'Admin' if self.cleaned_data['role'] == 'admin' else 'Student'
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        return user
