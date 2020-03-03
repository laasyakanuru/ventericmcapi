from django.contrib import admin

from Venter.models import (Category, File, Organisation, UserCategory,
                           UserComplaint)

class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('organisation_name',)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category',)

class FileAdmin(admin.ModelAdmin):
    list_display = ('organisation_name', 'ckpt_date')
    list_filter = ['organisation_name']

class UserCategoryAdmin(admin.ModelAdmin):
    list_display = ('user_category', 'creation_date')
    list_filter = ['organisation_name', 'creation_date']

class UserComplaintAdmin(admin.ModelAdmin):
    list_display = ('user_category', 'user_complaint')


admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(UserCategory, UserCategoryAdmin)
admin.site.register(UserComplaint, UserComplaintAdmin)
