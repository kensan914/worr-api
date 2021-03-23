from django.contrib import admin
from .models import *
from django.utils.html import format_html


@admin.register(TalkTicket)
class TalkTicketAdmin(admin.ModelAdmin):
    list_display = ('format_to_detail', 'owner', 'worry',
                    'format_status', 'wait_start_time', 'is_speaker', 'can_talk_heterosexual', 'can_talk_different_job', 'is_active')
    list_display_links = ('format_to_detail',)
    search_fields = ('owner__username',)
    date_hierarchy = 'wait_start_time'
    list_filter = ('worry', 'is_speaker', 'status', 'can_talk_heterosexual',
                   'can_talk_different_job', 'is_active')
    # filter_horizontal = ('genre_of_worries',
    #                      'blocked_accounts', 'talked_accounts')
    raw_id_fields = ('owner',)

    def format_to_detail(self, obj):
        return '詳細'
    format_to_detail.short_description = '詳細'

    def format_status(self, obj):
        if obj.status:
            backgroundColor = 'white'
            talk_status = TalkStatus(obj.status)
            if talk_status.name == 'TALKING':
                backgroundColor = 'palegreen'
            elif talk_status.name == 'WAITING':
                backgroundColor = 'lightskyblue'
            elif talk_status.name == 'STOPPING':
                backgroundColor = 'salmon'
            elif talk_status.name == 'FINISHING':
                backgroundColor = 'gold'
            elif talk_status.name == 'APPROVING':
                backgroundColor = 'mediumorchid'

            return format_html('<div style="background-color: {}; text-align: center; border-radius: 8px; padding-left: 2px; padding-right: 2px;">{}</div>', backgroundColor, talk_status.label)
        else:
            return 'No status'
    format_status.short_description = '状態'
    format_status.admin_order_field = 'status'


@admin.register(TalkingRoom)
class TalkingRoomAdmin(admin.ModelAdmin):
    list_display = ('format_to_detail', 'format_speaker_ticket', 'format_listener_ticket',
                    'started_at', 'ended_at', 'is_end', 'is_alert', 'is_time_out',)
    list_display_links = ('format_to_detail',)
    search_fields = ('speaker_ticket__owner__username',
                     'listener_ticket__owner__username',)
    date_hierarchy = 'started_at'
    list_filter = ('is_end', 'is_alert', 'is_time_out',)
    raw_id_fields = ('speaker_ticket', 'listener_ticket')

    def format_to_detail(self, obj):
        return '詳細'
    format_to_detail.short_description = '詳細'

    def format_speaker_ticket(self, obj):
        if obj.speaker_ticket:
            return obj.speaker_ticket.owner.username
        else:
            return 'No speaker'
    format_speaker_ticket.short_description = '話し手'
    format_speaker_ticket.admin_order_field = 'speaker_ticket'

    def format_listener_ticket(self, obj):
        if obj.listener_ticket:
            return obj.listener_ticket.owner.username
        else:
            return 'No listener'
    format_listener_ticket.short_description = '聞き手'
    format_listener_ticket.admin_order_field = 'listener_ticket'


@admin.register(MessageV2)
class MessageV2Admin(admin.ModelAdmin):
    list_display = ('format_to_detail', 'format_chat_composition',
                    'time', 'is_stored_on_speaker', 'is_stored_on_listener', 'is_read_speaker', 'is_read_listener')
    list_display_links = ('format_to_detail',)
    raw_id_fields = ('room', 'user')

    def format_to_detail(self, obj):
        return '詳細'
    format_to_detail.short_description = '詳細'

    def format_chat_composition(self, obj):
        if obj.room and obj.user:
            if obj.room.speaker_ticket.owner.id == obj.user.id:
                return '{}(話し手) ⏩ {}(聞き手)'.format(obj.room.speaker_ticket.owner, obj.room.listener_ticket.owner)
            elif obj.room.listener_ticket.owner.id == obj.user.id:
                return '{}(聞き手) ⏩ {}(話し手)'.format(obj.room.listener_ticket.owner, obj.room.speaker_ticket.owner)
