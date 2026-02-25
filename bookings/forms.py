from django import forms
from datetime import date
from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model  = Booking
        fields = ['facility', 'date', 'start_time', 'end_time']
        widgets = {
            'facility':   forms.Select(attrs={'class': 'form-select'}),
            'date':       forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time':   forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        # Accept a pre-selected facility from query param (?facility=<pk>)
        facility_id = kwargs.pop('facility_id', None)
        super().__init__(*args, **kwargs)
        # Only show active facilities in dropdown
        from facilities.models import Facility
        self.fields['facility'].queryset = Facility.objects.filter(is_active=True)
        if facility_id:
            self.fields['facility'].initial = facility_id

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('date')
        start_time   = cleaned_data.get('start_time')
        end_time     = cleaned_data.get('end_time')

        # 1. Date must not be in the past
        if booking_date and booking_date < date.today():
            raise forms.ValidationError('Booking date cannot be in the past.')

        # 2. end_time must be after start_time
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError('End time must be after start time.')

        return cleaned_data
