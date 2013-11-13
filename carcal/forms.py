from django import forms

from carcal.models import Calendar


class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ["name"]

    start_date = forms.DateField()
    end_date = forms.DateField()