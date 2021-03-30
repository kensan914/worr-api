from django.db.models import Q
from account.models import Gender, Job
from chat.models import TalkTicket, TalkStatus
from fullfii import create_talking_room, start_talk
from django.utils import timezone


def start_matching(version=2):
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

    def match_by_talk_tickets(talk_tickets_by_class):
        for talk_ticket in talk_tickets_by_class.filter(status=TalkStatus.WAITING, is_active=True).order_by('-wait_start_time'):
            if exists_matched_talk_tickets(talk_ticket):
                continue
            if talk_ticket.status != TalkStatus.WAITING:
                continue
            target_talk_tickets = search_target_talk_tickets(
                my_ticket=talk_ticket, talk_tickets=talk_tickets_by_class)  # 基本フィルタ
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

            matched_rooms.append(talking_room)
            # トーク開始
            if talking_room:
                print('start talk: ', talk_ticket, target_talk_ticket)
                start_talk(talking_room, version)

    # Accountをclass(ログイン頻度)ごとに分割(大宮開成スタイル)
    # [(Aクラス: 最終アクセス2日以内), (Bクラス: 最終アクセス4~7日以内), (Cクラス: それ以外)]
    # loggedin_minutes_class = [2*24*60, 7*24*60, -1]
    loggedin_minutes_class = [4*24*60, 7*24*60, -1]  # TODO:
    # [[(talkTicketA.pk), (talkTicketB.pk)], [(talkTicketC.pk), (talkTicketD.pk)], []]
    talk_ticket_ids_split_by_class = []
    for i in range(len(loggedin_minutes_class)):
        talk_ticket_ids_split_by_class.append([])

    for talk_ticket in TalkTicket.objects.all():
        elapsed_seconds = (
            timezone.now() - talk_ticket.owner.loggedin_at).total_seconds()
        elapsed_minutes = elapsed_seconds / 60

        for i, loggedin_minutes in enumerate(loggedin_minutes_class):
            if elapsed_minutes < loggedin_minutes:
                talk_ticket_ids_split_by_class[i].append(talk_ticket.pk)
                break
            elif loggedin_minutes == -1:
                talk_ticket_ids_split_by_class[i].append(talk_ticket.pk)
                break

    for talk_ticket_ids in talk_ticket_ids_split_by_class:
        talk_tickets = TalkTicket.objects.filter(pk__in=talk_ticket_ids)
        match_by_talk_tickets(talk_tickets)


def search_target_talk_tickets(my_ticket, talk_tickets):
    """
    条件に合うtarget_talk_ticketsを検索しクエリを返却
    基本フィルタ(worry, is_speaker)
    """
    return talk_tickets.exclude(owner=my_ticket.owner).filter(
        worry=my_ticket.worry,
        is_speaker=(not my_ticket.is_speaker),
        status=my_ticket.status,
        is_active=True,
    )


def filter_detail_target_talk_tickets(my_ticket, target_tickets):
    """
    詳細フィルタ(gender、 job, block, 過去にトーク済み)

    0. genderが "内緒" or "未設定" の場合、1・2は無視.
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

    if me.is_secret_gender or (me.gender != Gender.MALE and me.gender != Gender.FEMALE):  # 0
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
