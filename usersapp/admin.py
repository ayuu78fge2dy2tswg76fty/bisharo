from django.contrib import admin

# Register your models here.

from .models import userka

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'name', 'gender', 'created_at')
    search_fields = ('username', 'email', 'name')
    ordering = ('-username',)
admin.site.register(userka, UserAdmin)
