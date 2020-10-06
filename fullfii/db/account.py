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


def update_iap(iap, original_transaction_id=None, transaction_id=None, user=None, receipt=None, expires_date=None, status=None):
    iap.original_transaction_id = original_transaction_id if original_transaction_id is not None else iap.original_transaction_id
    iap.transaction_id = transaction_id if transaction_id is not None else iap.transaction_id
    iap.user = user if user is not None else iap.user
    iap.receipt = receipt if receipt is not None else iap.receipt
    iap.expires_date = expires_date if expires_date is not None else iap.expires_date
    iap.status = status if status is not None else iap.status
    iap.save()
    return iap
