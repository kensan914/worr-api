from django.db.models import Q
from account.models import Gender, Job
from chat.models import TalkTicket, TalkStatus, TalkingRoom
from fullfii import create_talking_room, start_talk


def start_matching():
    """
    マッチングシステム開始
    """
    matched_talk_tickets = []
    # matched_talk_ticketsに指定したtalk_ticketが存在するか

    def exists_matched_talk_tickets(_talk_ticket):
        for matched_talk_ticket in matched_talk_tickets:
            if matched_talk_ticket.id == _talk_ticket.id:
                return True
        return False

    matched_rooms = []
    # 同一のユーザマッチングの組み合わせが存在するか

    def exists_same_users_matching(_talk_ticket1, _talk_ticket2):
        for matched_room in matched_rooms:
            speaker_id = matched_room.speaker_ticket.owner.id
            listener_id = matched_room.listener_ticket.owner.id
            if (speaker_id == _talk_ticket1.owner.id and listener_id == _talk_ticket2.owner.id) or \
                    (speaker_id == _talk_ticket2.owner.id and listener_id == _talk_ticket1.owner.id):
                return True
        return False

    for talk_ticket in TalkTicket.objects.filter(status=TalkStatus.WAITING, is_active=True).order_by('-wait_start_time'):
        if exists_matched_talk_tickets(talk_ticket):
            continue
        if talk_ticket.status != TalkStatus.WAITING:
            continue
        target_talk_tickets = search_target_talk_tickets(
            my_ticket=talk_ticket)  # 基本フィルタ
        target_talk_tickets = filter_detail_target_talk_tickets(
            my_ticket=talk_ticket, target_tickets=target_talk_tickets)  # 詳細フィルタ
        if not target_talk_tickets.exists():
            continue

        # ↓マッチング↓
        target_talk_ticket = target_talk_tickets.order_by(
            '-wait_start_time').first()
        if exists_matched_talk_tickets(target_talk_ticket):
            continue
        if exists_same_users_matching(talk_ticket, target_talk_ticket):
            continue
        matched_talk_tickets.append(talk_ticket)
        matched_talk_tickets.append(target_talk_ticket)

        # talking room 作成
        talking_room = create_talking_room(
            talk_ticket if talk_ticket.is_speaker else target_talk_ticket,
            target_talk_ticket if talk_ticket.is_speaker else talk_ticket,
        )
        print('talking room 作成')
        print(TalkingRoom.objects.count())
        matched_rooms.append(talking_room)
        # トーク開始
        if talking_room:
            start_talk(talking_room)


def search_target_talk_tickets(my_ticket):
    """
    条件に合うtarget_talk_ticketsを検索しクエリを返却
    基本フィルタ(worry, is_speaker)
    """
    return TalkTicket.objects.exclude(owner=my_ticket.owner).filter(
        worry=my_ticket.worry,
        is_speaker=(not my_ticket.is_speaker),
        status=my_ticket.status,
        is_active=True,
    )


def filter_detail_target_talk_tickets(my_ticket, target_tickets):
    """
    詳細フィルタ(gender、 job, block, 過去にトーク済み)

    0. genderが"内緒"の場合、1・2は無視.
    1. my_ticketの「異性との相談を許可」がFalseの場合, 同性のみ.
    2. my_ticketの「異性との相談を許可」がTrueの場合, target_ticketsから「異性との相談を許可」がTrue, または同性をfilter
    3. jobが"内緒"の場合、4・5は無視.
    4. my_ticketの「異職業との相談を許可」がFalseの場合, 同職業のみ.
    5. my_ticketの「異職業との相談を許可」がTrueの場合, target_ticketsから「異職業との相談を許可」がTrue, または同職業をfilter
    6. ブロックしたユーザをexclude
    7. ブロックされているユーザをexclude
    8. 過去にトーク済みのユーザをexclude
    """
    me = my_ticket.owner
    blocked_accounts = me.blocked_accounts
    block_me_accounts = me.block_me_accounts
    talked_accounts = me.talked_accounts

    if me.gender == Gender.SECRET:  # 0
        pass
    elif not my_ticket.can_talk_heterosexual:  # 1
        target_tickets = target_tickets.filter(owner__gender=me.gender)
    else:  # 2
        target_tickets = target_tickets.filter(
            Q(can_talk_heterosexual=True) | Q(owner__gender=me.gender))

    if me.job == Job.SECRET:  # 3
        pass
    elif not my_ticket.can_talk_different_job:  # 4
        target_tickets = target_tickets.filter(owner__job=me.job)
    else:  # 5
        target_tickets = target_tickets.filter(
            Q(can_talk_different_job=True) | Q(owner__job=me.job))

    if blocked_accounts:  # 6
        target_tickets = target_tickets.exclude(
            owner__id__in=blocked_accounts.all().values_list('id', flat=True))
    if block_me_accounts:  # 7
        target_tickets = target_tickets.exclude(
            owner__id__in=block_me_accounts.all().values_list('id', flat=True))

    if talked_accounts:  # 8
        target_tickets = target_tickets.exclude(
            owner__id__in=talked_accounts.all().values_list('id', flat=True))

    return target_tickets
