from django.db import models

# Create your models here.

class rsid(models.Model):    
    rsid = models.CharField(max_length=20, default=None, blank=True)
    
    class Meta:
        app_label = 'annoquery'