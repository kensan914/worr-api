from chat.models import RoomV4


def get_created_rooms(target_user):
    # created_rooms (is_endはTrueでもFalseでも含め, 既にクローズされていれば含めない)
    return RoomV4.objects.filter(owner=target_user, is_active=True).exclude(
        closed_members=target_user
    )


def get_participating_rooms(target_user):
    # participating_rooms (is_endはTrueでもFalseでも含め, 既にクローズされていれば含めない)
    return RoomV4.objects.filter(participants=target_user, is_active=True).exclude(
        closed_members=target_user
    )
