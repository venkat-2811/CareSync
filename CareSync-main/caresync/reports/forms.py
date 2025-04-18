from django import forms
from .models import ReportFolder, Report

class ReportFolderForm(forms.ModelForm):
    class Meta:
        model = ReportFolder
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter folder name'}),
        }

class ReportForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter phone number'}))

    class Meta:
        model = Report
        fields = ['title', 'file', 'phone_number']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter report title'}),
            'file': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.csv'}),
        }

    def save(self, commit=True):
        report = super().save(commit=False)
        report.phone_number = self.cleaned_data['phone_number']  # Store phone number separately
        if commit:
            report.save()
        return report