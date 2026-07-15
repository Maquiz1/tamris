from django.db import models

class ActivableModel(models.Model):
    """
    A mixin to provide an 'is_active' boolean field.
    Inherit from this alongside TimeStampedModel when needed.
    """
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        abstract = True
