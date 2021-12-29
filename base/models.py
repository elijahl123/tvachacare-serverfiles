from .middleware import local

from django.db import models

from account.models import Account


class BaseModel(models.Model):
    creator = models.ForeignKey(Account, null=True, blank=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        if self.pk is None and hasattr(local, 'user'):
            self.creator = local.user
        return super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True