from django.db import models
import datetime
# get the current user
from django.contrib.auth import get_user_model

import logging
logger = logging.getLogger('django')
logger.setLevel(logging.INFO)

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

    def get_most_recent_note_history_with_history_hint(self):
        latest_note = self.get_most_recent_note_history_item()
        num_edits = len(self.get_all_note_history_items()) - 1
        plural = "s" if num_edits > 1 else ""
        hint = f'({num_edits} edit{plural})'

        return f'{latest_note} {hint}'

    def get_all_note_history_items(self):
        return self.note_history_reverse.all()         # type: ignore

    def get_all_note_history_items_as_formatted_string(self):
        return '\n'.join([str(x) for x in self.get_all_note_history_items()])

    def __str__(self):
        return f'Note: {self.pk}|{self.chr}:{self.start}-{self.stop}|{self.ref}->{self.alt}'

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
        logger.info(f'MODELS.PY: NoteHistoryModel.save() called for {self.pk} {self} with valid_to_date={self.valid_to_date} and valid_from_date={self.valid_from_date}')
        now = datetime.datetime.now()

        # If this is a new NoteHistoryModel instance, set valid_from_date to now
        if not self.pk:
            logger.info('SAVE_TRIGGER: if not self.pk = True')
            # Find the previous NoteHistoryModel instance for this NoteModel and set the valid to date
            try:
                prev_note_history = NoteHistoryModel.objects.filter(note=self.note).latest('valid_from_date')
                prev_note_history.valid_to_date = now
                prev_note_history.save()
                logger.info(f'SAVE_TRIGGER: saved prev_note_history {prev_note_history.pk}, {prev_note_history}')
                
            except NoteHistoryModel.DoesNotExist:
                pass

            # This is a new NoteHistoryModel instance, set valid_from_date to now and proceed to the end.
            self.valid_from_date = now
            # goes to the end
            return super().save(*args, **kwargs)

        else:
            logger.info('SAVE_TRIGGER: if not self.pk = False')
            # This is an existing NoteHistoryModel instance
            # Save the changes to a new instance
            # set valid_from_date to now, and save it
            
            # check if the valid_to_date has been changed and is not None. If it has, then just proceed with a normal save.
            matched_note = NoteHistoryModel.objects.filter(pk=self.pk).first()            
            if not matched_note: return

            logger.info(f'SAVE_TRIGGER: matched note: {matched_note.pk} {matched_note}')
            
            
            if (self.valid_to_date is not None) & (self.valid_to_date != matched_note.valid_to_date):
                # this branch means that the valid to date has already been set, so just proceed with a normal save.   
                logger.info('SAVE_TRIGGER: valid_to_date has already been set, so just proceed with a normal save.')
                return super().save(*args, **kwargs)
            # elif (self.clean_fields(exclude=['creator']) == matched_note.clean_fields(exclude=['creator'])) and (self.creator != matched_note.creator):
            #     logger.info('SAVE_TRIGGER: creator has changed, but other fields are the same. Proceeding with a normal save.')
            #     # this branch means that the creator has changed, but the other fields are the same. So just proceed with a normal save.
            #     return super().save(*args, **kwargs)
            else:
                # # if the valid to date has not been set, then assume that user is trying to overwrite this.
                # # trigger a new instance by removing the self.pk
                logger.info('SAVE_TRIGGER: valid_to_date has not been set, so assuming that user is trying to overwrite this. Triggering a new instance by removing the self.pk')
                self.pk = None 
                self.save()
                return 

        return super().save(*args, **kwargs)

            
        

    def get_valid_from_date(self):
        return self.valid_from_date.isoformat()    

    def get_short_date(self):
        return self.valid_from_date.strftime('%Y-%b-%d-%H:%M:%S')

    def get_valid_to_date(self):
        if self.valid_to_date:
            return self.valid_to_date.isoformat()
        else:
            return None

    def __str__(self):        
        return f'{self.creator.username} | {self.get_short_date()} | "{self.content}" ||'
        # return f'CN="{self.content}"|BY={self.creator.username},{self.creator.first_name},{self.creator.last_name}|CM={self.comment}|FR={self.get_valid_from_date()}|TO={self.get_valid_to_date()}|NT={self.note.note_id}|ID={self.notehistory_id}'
       