from django.contrib import admin
from .models import ReportFolder, Report

# Register your models here.

@admin.register(ReportFolder)
class ReportFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    list_filter = ('user',)
    search_fields = ('name', 'user__username')
    ordering = ('-created_at',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'folder', 'user', 'uploaded_at')
    list_filter = ('folder', 'user')
    search_fields = ('title', 'folder__name', 'user__username')
    ordering = ('-uploaded_at',)
