from django.db import models
import datetime

# Create your models here.

class NoteModel(models.Model):
    '''This is the model for the NoteModel.'''
    note_id = models.AutoField(primary_key=True)
    chr = models.CharField(max_length=32)
    start = models.IntegerField()
    stop = models.IntegerField()
    ref = models.CharField(max_length=64, blank=True, null=True)
    alt = models.CharField(max_length=64, blank=True, null=True)

    def get_most_recent_note_history_item(self):
        # use the ForeignKey reverse relation defined in the NoteHistoryModel class
        return self.note_history_reverse.latest('valid_from_date')         # type: ignore

    def get_all_note_history_items(self):
        return self.note_history_reverse.all()

    def __str__(self):
        return f'Note: {self.pk}|{self.chr}:{self.start}-{self.stop}->{self.alt}'

    class Meta:
        indexes = [
            models.Index(fields=['chr','start'])
        ]


class NoteHistoryModel(models.Model):
    '''This is the model for the NoteHistoryModel.'''
    notehistory_id = models.AutoField(primary_key=True)
    content = models.TextField()
    valid_from_date = models.DateTimeField(blank=True, editable=False, default=datetime.datetime.now)
    valid_to_date = models.DateTimeField(null=True, blank=True, editable=False)
    creator = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    comment = models.TextField(null=True, blank=True)
    note = models.ForeignKey(NoteModel, on_delete=models.PROTECT, related_name='note_history_reverse')

    def save(self, *args, **kwargs):
        now = datetime.datetime.now()

        # If this is a new NoteHistoryModel instance, set valid_from_date to now
        if not self.pk:
            # Find the previous NoteHistoryModel instance for this NoteModel and set the valid to date
            try:
                prev_note_history = NoteHistoryModel.objects.filter(note=self.note).latest('valid_from_date')
                prev_note_history.valid_to_date = now
                prev_note_history.save()
            except NoteHistoryModel.DoesNotExist:
                pass

            # This is a new NoteHistoryModel instance, set valid_from_date to now and proceed to the end.
            self.valid_from_date = now
            # goes to the end
            return super().save(*args, **kwargs)            

        else:
            # This is an existing NoteHistoryModel instance
            # Save the changes to a new instance
            # set valid_from_date to now, and save it
            
            # check if the valid_to_date has been changed and is not None. If it has, then just proceed with a normal save.
            matched_note = NoteHistoryModel.objects.filter(pk=self.pk).first()
            if not matched_note: return
            if (self.valid_to_date is not None) & (self.valid_to_date != matched_note.valid_to_date):
                # this branch means that the valid to date has already been set, so just proceed with a normal save.                
                return super().save(*args, **kwargs)
            else:
                # # if the valid to date has not been set, then assume that user is trying to overwrite this.
                # # trigger a new instance by removing the self.pk
                self.pk = None 
                self.save()
                return 

        return super().save(*args, **kwargs)

            
        

    def get_valid_from_date(self):
        return self.valid_from_date.isoformat()

    def get_valid_to_date(self):
        if self.valid_to_date:
            return self.valid_to_date.isoformat()
        else:
            return None

    def __str__(self):        
        return f'CN="{self.content}"|BY={self.creator.username},{self.creator.first_name},{self.creator.last_name}|CM={self.comment}|FR={self.get_valid_from_date()}|TO={self.get_valid_to_date()}|NT={self.note.note_id}|ID={self.notehistory_id}'
       