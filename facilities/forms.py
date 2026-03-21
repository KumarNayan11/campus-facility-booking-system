from django import forms

from users.models import Department

from .models import Facility


class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = [
            'name',
            'facility_type',
            'capacity',
            'amenities',
            'open_time',
            'close_time',
            'department',
            'max_pending_requests',
            'description',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS Lab 101'}),
            'facility_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'amenities': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. projector,AC,whiteboard',
            }),
            'open_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'close_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'max_pending_requests': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.order_by('name')
        self.fields['department'].required = False
