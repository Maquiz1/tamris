from django.urls import path
from . import views

app_name = 'medicines'

urlpatterns = [
    path('apply/initiate/<str:app_type>/', views.initiate_application_view, name='initiate_application'),
    path('apply/listing/<int:pk>/', views.medicine_listing_apply_view, name='apply_listing'),
    path('apply/category-ii/<int:pk>/', views.medicine_category_ii_apply_view, name='apply_category_ii'),
    path('payment/submit/<int:pk>/', views.applicant_payment_submission_view, name='submit_payment'),
    path('apply/edit/<int:pk>/', views.medicine_application_edit_view, name='edit_application'),
    path('staff/preliminary/', views.staff_preliminary_list_view, name='staff_preliminary_list'),
    path('staff/preliminary/<int:pk>/', views.staff_preliminary_detail_view, name='staff_preliminary_detail'),
    path('staff/payments/', views.staff_payment_list_view, name='staff_payment_list'),
    path('staff/payments/<int:pk>/', views.staff_payment_detail_view, name='staff_payment_detail'),
    path('staff/scientific/', views.staff_scientific_list_view, name='staff_scientific_list'),
    path('staff/scientific/<int:pk>/', views.staff_scientific_detail_view, name='staff_scientific_detail'),
    path('applicant/reports/', views.applicant_reports_view, name='applicant_reports'),
    path('applicant/payments/', views.applicant_payment_list_view, name='applicant_payment_list'),
    path('applicant/certificates/', views.applicant_certificate_list_view, name='applicant_certificate_list'),
    path('applicant/applications/', views.applicant_applications_view, name='applicant_applications'),
    path('applicant/listed/', views.applicant_listed_medicines_view, name='applicant_listed_medicines'),
    path('applicant/registered/', views.applicant_registered_medicines_view, name='applicant_registered_medicines'),
    path('applicant/application/<int:pk>/', views.applicant_application_detail_view, name='applicant_application_detail'),
    path('certificate/<int:pk>/', views.certificate_view, name='download_certificate'),
    path('staff/manage-fees/', views.finance_fee_configuration_view, name='finance_fee_configuration'),
    path('staff/inspections/', views.inspection_dashboard_view, name='inspection_dashboard'),
    path('staff/inspections/schedule/<int:app_id>/', views.schedule_inspection_view, name='schedule_inspection'),
    path('staff/inspections/report/<int:pk>/', views.submit_inspection_report_view, name='submit_inspection_report'),
    path('staff/inspections/detail/<int:pk>/', views.inspection_detail_view, name='inspection_detail'),
]
