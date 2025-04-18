from django.db import models
from django.utils import timezone
from home.models import CustomUser
import os
import json

def user_report_path(instance, filename):
    """Store reports under reports/<user_id>/"""
    # Use user_id if available, otherwise use phone_number as a fallback
    folder_name = str(instance.user.id) if instance.user else instance.phone_number
    return os.path.join('reports', folder_name, filename)


class ReportFolder(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='folders')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['name', 'user']

    def __str__(self):
        return f"{self.user.username}'s {self.name} folder"

class Report(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=user_report_path)
    folder = models.ForeignKey(ReportFolder, on_delete=models.CASCADE, related_name='reports')
    uploaded_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='reports', null=True, blank=True)
    phone_number = models.CharField(max_length=15)  # Keep this for backward compatibility
    analysis_data = models.JSONField(null=True, blank=True)  # Store the JSON analysis data

    def __str__(self):
        return self.title
    
    def save_analysis_data(self, data):
        """Save analysis data as JSON"""
        self.analysis_data = data
        self.save()
    
    def get_parameters(self):
        """Get all parameters from analysis data"""
        if not self.analysis_data or 'structured_data' not in self.analysis_data:
            return {}
        return self.analysis_data['structured_data']

class HealthParameter(models.Model):
    """Model to track health parameters over time"""
    phone_number = models.CharField(max_length=15)  # Keep for backward compatibility
    parameter_name = models.CharField(max_length=100)
    parameter_value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True, null=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='parameters')
    recorded_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['report', 'parameter_name']
        indexes = [
            models.Index(fields=['phone_number', 'parameter_name']),
        ]
    
    def __str__(self):
        return f"{self.parameter_name}: {self.parameter_value} {self.unit or ''}"

class ResourceLink(models.Model):
    """Model to store resource links from reports"""
    phone_number = models.CharField(max_length=15)  # Keep for backward compatibility
    title = models.CharField(max_length=255)
    url = models.URLField()
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='links')
    added_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        indexes = [
            models.Index(fields=['phone_number']),
        ]
    
    def __str__(self):
        return self.title