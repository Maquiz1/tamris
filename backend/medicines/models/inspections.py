from core.utils.uploads import inspection_document_path
from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from .applications import MedicineApplication

class InspectionSchedule(TimeStampedModel):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled (Imepangwa)'),
        ('COMPLETED', 'Completed (Imekamilika)'),
        ('CANCELLED', 'Cancelled (Imesitishwa)'),
    ]

    application = models.ForeignKey(MedicineApplication, on_delete=models.CASCADE, related_name='inspections')
    start_date_time = models.DateTimeField(verbose_name="Kuanza Ukaguzi (Start Date & Time)", null=True, blank=True)
    end_date_time = models.DateTimeField(verbose_name="Kumaliza Ukaguzi (End Date & Time)", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    assigned_inspectors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_inspections',
        blank=True,
        verbose_name="Assigned Inspectors (Wakaguzi waliopangwa)"
    )
    
    # Evaluator remarks
    evaluator_remarks_for_inspectors = models.TextField(blank=True, null=True, verbose_name="Remarks for Inspectors")
    evaluator_remarks_for_applicant = models.TextField(blank=True, null=True, verbose_name="Remarks for Applicant")
    
    # Checklist details
    check_manufacturing_area = models.BooleanField(default=False, verbose_name="Eneo la uzalishaji (Manufacturing area)")
    manufacturing_area_remarks = models.TextField(blank=True, null=True, verbose_name="Manufacturing Area Remarks")
    
    check_machines = models.BooleanField(default=False, verbose_name="Mashine (Machines)")
    machines_remarks = models.TextField(blank=True, null=True, verbose_name="Machines Remarks")
    
    check_cleanliness = models.BooleanField(default=False, verbose_name="Usafi (Cleanliness)")
    cleanliness_remarks = models.TextField(blank=True, null=True, verbose_name="Cleanliness Remarks")
    
    check_medicine_storage = models.BooleanField(default=False, verbose_name="Hifadhi ya dawa (Medicine storage)")
    medicine_storage_remarks = models.TextField(blank=True, null=True, verbose_name="Medicine Storage Remarks")
    
    check_quality_control = models.BooleanField(default=False, verbose_name="Mfumo wa udhibiti wa ubora (Quality control system)")
    quality_control_remarks = models.TextField(blank=True, null=True, verbose_name="Quality Control Remarks")

    # Report details
    report_file = models.FileField(upload_to=inspection_document_path, blank=True, null=True, verbose_name="Ripoti ya Ukaguzi (Inspection Report)")
    remarks = models.TextField(blank=True, null=True, verbose_name="Maoni ya Mkaguzi (Inspector Remarks)")
    gmp_compliant = models.BooleanField(default=False, verbose_name="Inakidhi Viwango (GMP Compliant?)")

    def __str__(self):
        return f"Inspection for {self.application.medicine_name}"

    class Meta:
        ordering = ['-start_date_time']
