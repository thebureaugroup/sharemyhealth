from django.contrib import admin
from .models import HIEProfile

# Copyright Videntity Systems Inc.

__author__ = "Alan Viars"


class HIEProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'subject', 'mrn','updated_at')
    search_fields = [
        'user__first_name',
        'user__last_name',
        'mrn', ]
    raw_id_fields = ("user", )


admin.site.register(HIEProfile, HIEProfileAdmin)
