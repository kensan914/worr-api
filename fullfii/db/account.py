from django.db.models import Q
from account.models import Account, Iap, IapStatus, Gender


def get_all_accounts(me=None):
    """
    全ての利用者アカウントを取得. me指定で除外可
    """
    accounts = Account.objects.filter(is_active=True, is_staff=False, is_superuser=False)
    if me:
        return accounts.exclude(id=me.id)
    else:
        return accounts

def get_viewable_accounts(me, is_exclude_me=False):
    """
    全ての利用者アカウント(性別・ブロックを考慮)を取得. is_exclude_me指定で除外可
    0. genderが"内緒"の場合、1・2は無視しall_accountsを返す(ブロック処理はする)
    1. 自分の「異性との相談を許可」がFalseの場合, 同性のみ.
    2. 自分の「異性との相談を許可」がTrueの場合, 全利用者アカウントから「異性との相談を許可」がTrue, または同性をfilter
    3. ブロックしたユーザをexclude
    4. ブロックされているユーザをexclude
    """
    can_talk_heterosexual = me.can_talk_heterosexual
    gender = me.gender
    blocked_accounts = me.blocked_accounts
    block_me_accounts = me.block_me_accounts

    def exclude_block_accounts(_accounts):
        if blocked_accounts:  # 3
            _accounts = _accounts.exclude(id__in=blocked_accounts.all().values_list('id', flat=True))
        if block_me_accounts:  # 4
            _accounts = _accounts.exclude(id__in=block_me_accounts.all().values_list('id', flat=True))
        return _accounts

    # all_accounts = get_all_accounts(me=me if is_exclude_me else None).exclude(Q(birthday=None) | Q(gender=None))
    # birthday, gender未設定でも表示対象に加える
    all_accounts = get_all_accounts(me=me if is_exclude_me else None)
    if gender == Gender.SECRET:  # 0
        return exclude_block_accounts(all_accounts)
    if not can_talk_heterosexual:  # 1
        accounts = all_accounts.filter(gender=gender)
    else:  # 2
        accounts = all_accounts.filter(Q(can_talk_heterosexual=True) | Q(gender=gender))

    return exclude_block_accounts(accounts)


def increment_num_of_thunks(user):
    user.num_of_thunks += 1
    user.save()


def create_iap(original_transaction_id, transaction_id, user, receipt, expires_date):
    iap = Iap(
        original_transaction_id=original_transaction_id,
        transaction_id=transaction_id,
        user=user,
        receipt=receipt,
        expires_date=expires_date,
        status=IapStatus.SUBSCRIPTION,
    )
    iap.save()
    return iap


def update_iap(iap, original_transaction_id=None, transaction_id=None, user=None, receipt=None, expires_date=None, status=None):
    iap.original_transaction_id = original_transaction_id if original_transaction_id is not None else iap.original_transaction_id
    iap.transaction_id = transaction_id if transaction_id is not None else iap.transaction_id
    iap.user = user if user is not None else iap.user
    iap.receipt = receipt if receipt is not None else iap.receipt
    iap.expires_date = expires_date if expires_date is not None else iap.expires_date
    iap.status = status if status is not None else iap.status
    iap.save()
    return iap
