from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from .applications import MedicineApplication

class MedicineEvaluation(TimeStampedModel):
    application = models.OneToOneField(MedicineApplication, on_delete=models.CASCADE, related_name='evaluation')
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='evaluations_conducted')
    
    # Preliminary Screening (Uhakiki wa Awali)
    documents_complete = models.BooleanField(default=False, verbose_name="Completeness of documents (Kukagua ukamilifu wa nyaraka)")
    documents_remarks = models.TextField(blank=True, null=True)
    
    # Scientific Evaluation (Tathmini ya Kisayansi)
    quality_check = models.BooleanField(default=False, verbose_name="Quality of medicine (Ubora wa dawa)")
    quality_remarks = models.TextField(blank=True, null=True)
    
    safety_check = models.BooleanField(default=False, verbose_name="Safety of medicine (Usalama wa dawa)")
    safety_remarks = models.TextField(blank=True, null=True)
    
    efficacy_check = models.BooleanField(default=False, verbose_name="Efficacy of medicine (Ufanisi wa dawa)")
    efficacy_remarks = models.TextField(blank=True, null=True)
    
    validity_of_tests = models.BooleanField(default=False, verbose_name="Validity of tests (Uhalali wa vipimo)")
    validity_remarks = models.TextField(blank=True, null=True)
    
    label_inspection = models.BooleanField(default=False, verbose_name="Label inspection (Ukaguzi wa lebo)")
    label_remarks = models.TextField(blank=True, null=True)
    
    gmp_inspection_check = models.BooleanField(default=False, verbose_name="GMP Inspection (Ukaguzi wa eneo la uzalishaji)")
    gmp_inspection_remarks = models.TextField(blank=True, null=True)
    
    overall_comments = models.TextField(blank=True, null=True, verbose_name="Overall Evaluation Comments")
    sections_to_revise = models.JSONField(default=list, blank=True, verbose_name="Sections allowed to be edited by applicant")

    def __str__(self):
        return f"Evaluation for {self.application.medicine_name}"

