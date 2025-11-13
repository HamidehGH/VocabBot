from django.contrib import admin
from .forms import AdminUserProfileForm
from .models import Vocabulary,UserVocabularyProgress, UserProfile, VocabularyImage

admin.site.register(UserVocabularyProgress)

class AdminUserProfile(admin.ModelAdmin):
    form = AdminUserProfileForm
admin.site.register(UserProfile , AdminUserProfile)


class VocabularyAdminImageInline(admin.StackedInline):
    model = VocabularyImage
    fields = ['image', 'caption']
    extra = 1                     
    can_delete = True  


class VocabularyAdmin(admin.ModelAdmin):
    list_display = ['word', 'meaning', 'user', 'date_added']
    search_fields = ['word', 'meaning', 'description']
    list_filter = ['user', 'date_added']
    inlines = [VocabularyAdminImageInline] 

admin.site.register(Vocabulary, VocabularyAdmin)









