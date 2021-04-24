from survey.models import AccountDeleteSurvey
from django.contrib import admin


@admin.register(AccountDeleteSurvey)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('respondent', 'reason')
    list_display_links = ('respondent',)
    search_fields = ('respondent__username', 'reason',)
    date_hierarchy = 'created_at'
    raw_id_fields = ('respondent',)
