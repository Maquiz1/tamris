from django.urls import path
from . import views

app_name = 'medicines'

urlpatterns = [
    path('apply/initiate/<str:app_type>/', views.initiate_application_view, name='initiate_application'),
    path('apply/master/<int:pk>/', views.medicine_master_apply_view, name='apply_master'),
    path('payment/submit/<int:pk>/', views.applicant_payment_submission_view, name='submit_payment'),
    path('apply/edit/<int:pk>/', views.medicine_application_edit_view, name='edit_application'),
    path('apply/upgrade/<int:pk>/', views.upgrade_to_registration_view, name='upgrade_to_registration'),
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
    path('provisional-letter/<int:pk>/', views.provisional_letter_view, name='provisional_letter'),
    path('renew/<int:pk>/', views.start_renewal_view, name='start_renewal'),
    path('claim/<int:legacy_user_id>/', views.legacy_claim_request_view, name='legacy_claim_request'),
    path('staff/manage-fees/', views.finance_fee_configuration_view, name='finance_fee_configuration'),
    path('staff/inspections/', views.inspection_dashboard_view, name='inspection_dashboard'),
    path('staff/inspections/schedule/<int:app_id>/', views.schedule_inspection_view, name='schedule_inspection'),
    path('staff/inspections/report/<int:pk>/', views.submit_inspection_report_view, name='submit_inspection_report'),
    path('staff/inspections/detail/<int:pk>/', views.inspection_detail_view, name='inspection_detail'),

    # Registrar (approves certificates on behalf of the Committee)
    path('registrar/', views.registrar_dashboard_view, name='registrar_dashboard'),
    path('registrar/final-approvals/', views.final_approval_list_view, name='final_approval_list'),
    path('registrar/final-approvals/<int:pk>/', views.final_approval_detail_view, name='final_approval_detail'),
    path('registrar/legacy/', views.legacy_verification_list_view, name='legacy_verification_list'),
    path('registrar/legacy/<int:pk>/', views.legacy_verification_detail_view, name='legacy_verification_detail'),
    path('registrar/link-requests/', views.claim_list_view, name='claim_list'),

    # Data Clerk (records from before the system)
    path('legacy/', views.legacy_dashboard_view, name='legacy_dashboard'),
    path('legacy/applicants/new/', views.legacy_applicant_create_view, name='legacy_applicant_create'),
    path('legacy/medicines/new/', views.legacy_medicine_create_view, name='legacy_medicine_create'),
    path('legacy/medicines/<int:pk>/edit/', views.legacy_medicine_create_view, name='legacy_medicine_edit'),

    # Administrator
    path('staff/settings/', views.system_settings_view, name='system_settings'),
]
