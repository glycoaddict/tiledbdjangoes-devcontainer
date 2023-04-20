from typing import Any
from django.contrib import admin
from django.http import HttpRequest, HttpResponseRedirect
from tilequery.models import *

# Register your models here.

class NoteHistoryInline(admin.TabularInline):
    model = NoteHistoryModel
    extra=0
    

@admin.register(NoteModel)
class NoteAdmin(admin.ModelAdmin):
    # change_form_template = 'admin/notemodel_change.html'
    list_display = ('note_id', 'chr', 'start', 'stop', 'ref', 'alt', 'get_most_recent_note_history_item', 'get_all_note_history_items')
    fields = ('chr', 'start', 'stop', 'ref', 'alt')
    

    def most_recent_note_history_item(self, obj):
        note_history = obj.get_most_recent_note_history_item()
        return note_history.content if note_history else ''

    # def save_model(self, request, obj, form, change):
    #     print(f'save_model user = {request.user}')
    #     # obj.user = User.objects.get(username=request.user)
    #     obj.creator = request.user        
        
    #     return super(NoteAdmin, self).save_model(request, obj, form, change)

    most_recent_note_history_item.short_description = 'Most recent NoteHistory'
    inlines = [NoteHistoryInline]
    

@admin.register(NoteHistoryModel)
class NoteHistoryAdmin(admin.ModelAdmin):
    list_display = ('notehistory_id', 'content', 'creator', 'comment', 'note')
    readonly_fields = ('valid_from_date', 'valid_to_date')
    pass


# admin.site.register(NoteModel, NoteAdmin)