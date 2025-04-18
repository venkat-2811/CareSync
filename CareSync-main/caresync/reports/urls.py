from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.folder_list, name='folder_list'),
    path('create/', views.folder_create, name='folder_create'),
    path('<int:folder_id>/', views.folder_detail, name='folder_detail'),
    path('report/delete/<int:report_id>/', views.report_delete, name='report_delete'),
    path('folder/delete/<int:folder_id>/', views.folder_delete, name='folder_delete'),
    path('report/analysis/<int:report_id>/', views.report_analysis, name='report_analysis'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
]