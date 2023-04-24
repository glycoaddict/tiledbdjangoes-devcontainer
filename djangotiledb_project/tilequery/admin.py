from typing import Any
from django.contrib import admin
from django.http import HttpRequest, HttpResponseRedirect, HttpResponseBadRequest
from django.urls import path
from urllib.parse import urlencode
import logging
from django.forms import BaseInlineFormSet

from tilequery.models import *

logger = logging.getLogger('django')
logger.setLevel(logging.INFO)

# Register your models here.

class NoteHistoryInline(admin.TabularInline):
    model = NoteHistoryModel
    # set which fields to show in the inline
    fields = ('pk', 'content', 'creator', 'comment')
    # set the readonly fields
    readonly_fields = ('pk',)
    # order the records by valid_from_date
    ordering = ('-valid_from_date',)
    # set the number of extra rows to show
    extra = 0
    
    

@admin.register(NoteModel)
class NoteAdmin(admin.ModelAdmin):
    # change_form_template = 'admin/notemodel_change.html'
    list_display = ('note_id', 'chr', 'start', 'stop', 'ref', 'alt', 'get_most_recent_note_history_item', 'get_all_note_history_items_as_formatted_string')
    fields = ('chr', 'start', 'stop', 'ref', 'alt')
    
    def most_recent_note_history_item(self, obj):
        note_history = obj.get_most_recent_note_history_item()
        return note_history.content if note_history else ''
    
    most_recent_note_history_item.short_description = 'Most recent NoteHistory'
    inlines = [NoteHistoryInline]
    
    def save_formset(self, request: Any, form: Any, formset: BaseInlineFormSet, change: Any) -> None:
        # to_change = [f for f in formset if f.has_changed() and f.is_valid()]
        # for tc in to_change:
        #     tc.cleaned_data['creator'] = request.user
        #     logger.info(f'ADMIN.PY: save_formset: formset has changed and is valid, {tc.cleaned_data}')

        fnew = formset
        for f in fnew:
            # logger.info(f'ADMIN.PY: save_formset: {f.cleaned_data}')
            if f.has_changed() and f.is_valid():
                f.cleaned_data['creator'] = request.user
                f.cleaned_data['valid_to_date'] = None
                # update the instance with the new creator
                f.instance.creator = request.user
                f.instance.valid_to_date = None
                
                logger.info(f'ADMIN.PY: save_formset: formset has changed and is valid, {f.cleaned_data}')

        # saved_formset = fnew.save(commit=False)
        
        
        return super().save_formset(request, form, fnew, change)

    def save_related(self, request: Any, form: Any, formsets: Any, change: Any) -> None:        
        # Here, i want to override the creator field of the NoteHistoryModel.
        # however, triggering save() creates a duplicate because in models.py, the NoteHistoryModel is set 
        # to create a new instance on save() if the pk is already set.
        logger.info('ADMIN.PY: save_related was called')
        
        # # this step will save any changes to NoteHistoryModel and NoteModel
        super().save_related(request, form, formsets, change)

        # # next we want to enforce creator
        
        # for formset in formsets:
        #     if isinstance(formset, BaseInlineFormSet) and 'NoteHistoryModelFormFormSet' in str(type(formset.__class__())):
        #         logger.info('found NoteHistoryModelFormFormSet') 
                            
        #         for form in formset.forms:
        #             # logger.info(f"form: {form.instance.pk}, {form.instance}")
        #             # check if the form has an instance, ie is existing
        #             if form.instance.pk:
        #                 # Check if the form has been changed and is valid
        #                 if form.has_changed() and form.is_valid():
        #                     logger.info(f"CHANGED {form.instance.pk}, {form.instance}")
        #                     # Save the form and get the saved object
        #                     form.instance.creator = request.user
        #                     note_history = form.save()
        #                     # Do something with the saved object
        #                     logger.info(f"Saved note history object <{note_history.pk}> and overrid user to <{note_history.creator}>")
        

    # def get_urls(self):
    #     urls = super().get_urls()
    #     custom_urls = [
    #         path('create_from_post/', self.create_from_post, name='create_from_post'),
    #     ]
    #     return custom_urls + urls

    # def create_from_post(self, request):
    #     # if request.method == 'POST':  
    #     if True:   
    #         data = request.POST
    #         new_note = NoteModel(
    #             chr=data.get('chr', None),
    #             start=data.get('start', None),
    #             stop=data.get('stop', None),
    #             ref=data.get('ref', None),
    #             alt=data.get('alt', None),
    #         )
    #         form = self.get_form(request)(instance=new_note)
    #         query_string = urlencode(form.initial)
    #         return HttpResponseRedirect('/admin/tilequery/notemodel/add/?%s' % query_string)
    #     else:
    #         return HttpResponseBadRequest('Bad Request')
   

    
    

@admin.register(NoteHistoryModel)
class NoteHistoryAdmin(admin.ModelAdmin):
    list_display = ('notehistory_id', 'content', 'creator', 'comment', 'note')
    readonly_fields = ('valid_from_date', 'valid_to_date')

    def save_model(self, request: Any, obj: Any, form: Any, change: Any) -> None:
        logger.debug(f'save_model: {form}')
        obj.creator = request.user
        obj.valid_to_date = None
        return super().save_model(request, obj, form, change)