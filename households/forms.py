from django import forms

from .models import Household, Invite


class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = ["name", "type", "timezone"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Sunset Flat"}),
            "timezone": forms.TextInput(attrs={"placeholder": "UTC"}),
        }


class InviteForm(forms.ModelForm):
    class Meta:
        model = Invite
        fields = ["email", "role"]
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "guest@example.com"})
        }
