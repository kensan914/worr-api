from account.models import Account

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
