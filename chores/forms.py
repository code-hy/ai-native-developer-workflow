from django import forms

from .models import Chore


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = [
            "title",
            "description",
            "category",
            "effort",
            "minutes",
            "assignee",
            "rrule",
            "due_at",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Take out trash"}),
            "description": forms.Textarea(attrs={"rows": 2}),
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "rrule": forms.TextInput(attrs={"placeholder": "FREQ=WEEKLY;BYDAY=MO"}),
        }

    def __init__(self, *args, household=None, **kwargs):
        super().__init__(*args, **kwargs)
        if household is not None:
            # limit assignee to household members
            from households.models import Membership

            user_ids = Membership.objects.filter(household=household).values_list(
                "user_id", flat=True
            )
            self.fields["assignee"].queryset = self.fields["assignee"].queryset.filter(
                id__in=user_ids
            )
            self.fields["assignee"].required = False
            self.fields["assignee"].empty_label = "— Unassigned (pool) —"

    def clean_effort(self):
        v = self.cleaned_data["effort"]
        if not 1 <= v <= 5:
            raise forms.ValidationError("Effort must be 1-5")
        return v
