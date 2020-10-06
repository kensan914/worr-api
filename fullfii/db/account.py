from account.models import Account, Iap, IapStatus

"""
fullfii/__init__.pyによるimport * を制限(循環importを引き起こす)
"""

def get_all_accounts(me=None):
    accounts = Account.objects.filter(is_active=True, is_staff=False, is_superuser=False)
    if me:
        return accounts.exclude(id=me.id)
    else:
        return accounts


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
