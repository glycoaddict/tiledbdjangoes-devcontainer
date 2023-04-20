from django.db import models

# Create your models here.

class Snps(models.Model):    
    rsid = models.CharField(max_length=16)
    chr = models.CharField(max_length=32)
    start = models.IntegerField()
    stop = models.IntegerField()
    ref = models.CharField(max_length=64, blank=True, null=True)
    alt = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        app_label = 'annoquery'
        indexes = [
            models.Index(fields=['chr','start'])
        ]

        

class Clinvars(models.Model):
    """Records must be unique based on [alleleid,order]"""
    
    alleleid = models.IntegerField()
    type = models.CharField(max_length=25)
    name = models.CharField(max_length=800)
    geneid = models.IntegerField()
    genesymbol = models.CharField(max_length=710)
    hgnc_id = models.CharField(max_length=10)
    clinicalsignificance = models.CharField(max_length=70)
    clinsigsimple = models.IntegerField()
    lastevaluated = models.CharField(max_length=12)
    rsid = models.IntegerField() # may want to foreign key this?
    nsvesv = models.CharField(max_length=10) # originally `nsv/esv (dbVar)` column
    rcvaccession = models.CharField(max_length=597)
    phenotypeids = models.CharField(max_length=4300) # originally 4233
    phenotypelist = models.CharField(max_length=1450) # originally 4233
    origin = models.CharField(max_length=55)
    originsimple = models.CharField(max_length=19)
    assembly = models.CharField(max_length=6)
    chromosomeaccession = models.CharField(max_length=14)
    chromosome = models.CharField(max_length=4)
    start = models.IntegerField()
    stop = models.IntegerField()
    referenceallele = models.CharField(max_length=12)
    alternateallele = models.CharField(max_length=20)
    cytogenetic = models.CharField(max_length=24)
    reviewstatus = models.CharField(max_length=52)
    numbersubmitters = models.IntegerField() # original 66
    guidelines = models.CharField(max_length=35)
    testedingtr = models.CharField(max_length=1)
    otherids = models.CharField(max_length=4035)
    submittercategories = models.IntegerField()
    variationid = models.IntegerField()
    positionvcf = models.IntegerField()
    referenceallelevcf = models.CharField(max_length=100) # will truncate longer deletions, but will be captured anyway by start and stop
    alternateallelevcf = models.CharField(max_length=100) # will truncate longer insertions, but will be captured anyway by start and stop
    order = models.FloatField()

    def __repr__(self) -> str:
        return super().__repr__() + f'//{self.clinicalsignificance}//{self.genesymbol}//{self.chromosome}:{self.start}-{self.stop}'
    
    class Meta:
        app_label = 'annoquery'
        indexes = [
            models.Index(fields=['chromosome','start']),
            models.Index(fields=['clinicalsignificance']),
        ]


class Genes(models.Model):
    chromosome = models.IntegerField()
    source = models.CharField(max_length=19, null=True, blank=True)
    gene_type = models.CharField(max_length=21, null=True, blank=True)
    start = models.IntegerField()
    stop = models.IntegerField()
    gene = models.CharField(max_length=127, null=True, blank=True)
    product = models.CharField(max_length=160, null=True, blank=True)
    
    class Meta:
        app_label = 'annoquery'
        indexes = [
            models.Index(fields=['chromosome','start']),
        ]
