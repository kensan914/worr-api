from django.contrib import admin
from .models import *
from django.utils.html import format_html
import fullfii


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'format_gender', 'job', 'num_of_thunks',
                    'format_genre_of_worries', 'introduction', 'is_active', 'loggedin_at', 'date_joined')
    list_display_links = ('username',)
    search_fields = ('username',)
    date_hierarchy = 'date_joined'
    list_filter = ('gender', 'is_secret_gender', 'job', 'is_active')
    filter_horizontal = ('genre_of_worries',
                         'blocked_accounts', 'talked_accounts')

    def format_gender(self, obj):
        if obj.gender is not None and obj.is_secret_gender is not None:
            if obj.is_secret_gender:
                return '内緒'
            else:
                return Gender(obj.gender).label
    format_gender.short_description = '性別'
    format_gender.admin_order_field = 'gender'

    def format_genre_of_worries(self, obj):
        genre_of_worries_labels = [
            gow.label for gow in obj.genre_of_worries.all()]
        return '・'.join(genre_of_worries_labels)
    format_genre_of_worries.short_description = '悩み'
    format_genre_of_worries.admin_order_field = 'genre_of_worries'


@admin.register(ProfileImage)
class ProfileImageAdmin(admin.ModelAdmin):
    list_display = ('format_picture', 'user', 'upload_date')
    list_display_links = ('format_picture',)
    search_fields = ('user__username',)
    date_hierarchy = 'upload_date'
    raw_id_fields = ('user',)

    def format_picture(self, obj):
        if obj.picture:
            if fullfii.exists_profile_std_image(obj.picture):
                img_src = obj.picture.thumbnail.url
            else:
                img_src = obj.picture.url
            return format_html('<img src="{}" width="100" style="border-radius: 8px" />', img_src)
    format_picture.short_description = '画像'
    format_picture.empty_value_display = 'No image'


@admin.register(GenreOfWorries)
class GenreOfWorriesAdmin(admin.ModelAdmin):
    list_display = ('label', 'key', 'value')
    list_display_links = ('label',)
    search_fields = ('label',)
