from django import forms
from django.utils import timezone

from .models import BookingRequest


class BookingRequestForm(forms.ModelForm):
    """Form for users to submit a new booking request."""

    class Meta:
        model = BookingRequest
        fields = ['facility', 'start_datetime', 'end_datetime', 'purpose']
        widgets = {
            'facility': forms.Select(attrs={'class': 'form-select'}),
            'start_datetime': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'end_datetime': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'e.g. Lab session for CS301 - 3rd year students',
            }),
        }

    def __init__(self, *args, **kwargs):
        facility_id = kwargs.pop('facility_id', None)
        super().__init__(*args, **kwargs)

        from facilities.models import Facility

        self.fields['facility'].queryset = Facility.objects.filter(is_active=True)
        self.fields['start_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        if facility_id:
            self.fields['facility'].initial = facility_id

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')

        if start_datetime and timezone.is_naive(start_datetime):
            start_datetime = timezone.make_aware(start_datetime, timezone.get_current_timezone())
            cleaned_data['start_datetime'] = start_datetime
        if end_datetime and timezone.is_naive(end_datetime):
            end_datetime = timezone.make_aware(end_datetime, timezone.get_current_timezone())
            cleaned_data['end_datetime'] = end_datetime

        if start_datetime and end_datetime and end_datetime <= start_datetime:
            raise forms.ValidationError('End date and time must be after the start date and time.')

        return cleaned_data


class RejectRequestForm(forms.Form):
    """Simple form for the manager to optionally supply a rejection reason."""

    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional: reason for rejection (visible to the requester)',
        }),
        label='Rejection Reason',
    )
