from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    """
    Extends Django's built-in UserCreationForm with email + role selection.

    Email is stored on Django's built-in User model — no custom model needed.
    This makes future OAuth / allauth integration straightforward: the OAuth
    backend simply sets User.email without changing any schema.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    role = forms.ChoiceField(
        choices=[
            ('user', 'User'),
            ('manager', 'Manager'),
        ],
        initial='user',
        help_text='Users can submit booking requests. Managers govern the system.',
        widget=forms.Select(attrs={'class': 'form-select'}),
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
            group_name = self.cleaned_data['role'].capitalize()
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        return user
