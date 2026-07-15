from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard_view, name='dashboard'),
    path('applications/', views.applications_report_view, name='applications'),
    path('payments/', views.payments_report_view, name='payments'),
    path('medicines/', views.medicines_report_view, name='medicines'),
    path('users/', views.users_report_view, name='users'),
    path('evaluations/', views.evaluations_report_view, name='evaluations'),
    path('inspections/', views.inspections_report_view, name='inspections'),
]
