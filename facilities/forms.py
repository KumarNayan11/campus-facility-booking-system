from django import forms
from .models import Facility


class FacilityForm(forms.ModelForm):
    class Meta:
        model  = Facility
        fields = ['name', 'facility_type', 'capacity', 'description', 'is_active']
        widgets = {
            'name':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS Lab 101'}),
            'facility_type': forms.Select(attrs={'class': 'form-select'}),
            'capacity':      forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'description':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active':     forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
