from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'score', 'created_at')
    search_fields = ('book__title', 'user__username', 'text')
    list_filter = ('score', 'created_at')
