from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from account.models import Plan, Iap, IapStatus
import requests
from account.serializers import MeSerializer
from fullfii import create_iap
from fullfii.lib.constants import IAP_SHARED_SECRET, IAP_STORE_API_URL, IAP_STORE_API_URL_SANDBOX, BUNDLE_ID
from fullfii.lib.support import cvt_tz_str_to_datetime


def request_post_receipt(receipt):
    post_data = {
        'receipt-data': receipt,
        'password': IAP_SHARED_SECRET,
        'exclude-old-transactions': True,
    }
    res = requests.post(IAP_STORE_API_URL, json=post_data)
    res_json = res.json()

    if res_json['status'] == 21007:  # sandbox
        res = requests.post(IAP_STORE_API_URL_SANDBOX, json=post_data)
        res_json = res.json()

    return res_json


def format_verify_receipt_json(res_json):
    """
    :param res_json:
    :return: {'status': ..., 'bundle_id': ..., 'original_transaction_id': ..., 'transaction_id': ...,
            'latest_receipt': ..., 'expires_date': ..., 'is_in_billing_retry_period': ...(if not exists, -1),
            'auto_renew_status': ...}
    """
    receipt_data = {
        'status': res_json['status'],
        'bundle_id': res_json['receipt']['bundle_id'],
        'original_transaction_id': res_json['latest_receipt_info'][0]['original_transaction_id'],
        'transaction_id': res_json['latest_receipt_info'][0]['transaction_id'],
        'latest_receipt': res_json['latest_receipt'],
        'expires_date': res_json['latest_receipt_info'][0]['expires_date'],
        'is_in_billing_retry_period': res_json['pending_renewal_info'][0]['is_in_billing_retry_period'] if 'is_in_billing_retry_period' in res_json['pending_renewal_info'][0] else '-1',
        'auto_renew_status': res_json['pending_renewal_info'][0]['auto_renew_status'],
    }

    return receipt_data



def verify_receipt_when_purchase(product_id, receipt, user):
    if not product_id in Plan.values:
        return Response({'type': 'not_found', 'message': "not found plan"}, status=status.HTTP_404_NOT_FOUND)

    res_json = request_post_receipt(receipt)
    receipt_data = format_verify_receipt_json(res_json)
    print(receipt_data)

    if receipt_data['status'] != 0:
        return Response({'type': 'failed_verify_receipt', 'message': "bad status"}, status=status.HTTP_409_CONFLICT)
    if receipt_data['bundle_id'] != BUNDLE_ID:
        return Response({'type': 'failed_verify_receipt', 'message': "bad bundle ID"}, status=status.HTTP_409_CONFLICT)
    if Iap.objects.filter(original_transaction_id=receipt_data['original_transaction_id']).exists():
        return Response({'type': 'failed_verify_receipt', 'message': "the original transaction ID already exists"},
                        status=status.HTTP_409_CONFLICT)
    if Iap.objects.filter(transaction_id=receipt_data['transaction_id']).exists():
        return Response({'type': 'failed_verify_receipt', 'message': "the transaction ID already exists"},
                        status=status.HTTP_409_CONFLICT)
    if Iap.objects.filter(user=user).exists():
        return Response({'type': 'failed_verify_receipt', 'message': "the user already exists"},
                        status=status.HTTP_409_CONFLICT)

    create_iap(
        original_transaction_id=receipt_data['original_transaction_id'],
        transaction_id=receipt_data['transaction_id'],
        user=user,
        receipt=receipt_data['latest_receipt'],
        expires_date=cvt_tz_str_to_datetime(receipt_data['expires_date']),
    )
    user.plan = product_id
    user.save()
    return Response({'status': 'success', 'profile': MeSerializer(user).data}, status=status.HTTP_200_OK)


def verify_receipt_when_update(verified_iap):
    res_json = request_post_receipt(verified_iap.receipt)
    receipt_data = format_verify_receipt_json(res_json)
    # print(res_json)

    if receipt_data['status'] != 0:
        return

    # case 1. 自動更新に成功している
    if not Iap.objects.filter(transaction_id=receipt_data['transaction_id']).exists():
        print('case 1')
        verified_iap.transaction_id = receipt_data['transaction_id']
        verified_iap.receipt = receipt_data['latest_receipt']
        verified_iap.expires_date = cvt_tz_str_to_datetime(receipt_data['expires_date'])

    # case 2. まだ更新に成功していないが、今後成功する可能性がある
    elif receipt_data['is_in_billing_retry_period'] == '1':
        print('case 2')
        verified_iap.receipt = receipt_data['latest_receipt']
        verified_iap.status = IapStatus.FAILURE

    # case 3. その購読は自動更新されない
    elif receipt_data['is_in_billing_retry_period'] == '0' or receipt_data['auto_renew_status'] == '0':
        print('case 3')
        verified_iap.receipt = receipt_data['latest_receipt']
        verified_iap.status = IapStatus.EXPIRED
        verified_iap.user.plan = Plan.FREE
        verified_iap.user.save()

    verified_iap.save()


def manage_iap_expires_date(within_minutes=720):
    subscription_iaps = Iap.objects.filter(status=IapStatus.SUBSCRIPTION)

    for subscription_iap in subscription_iaps:
        deadline_seconds = (subscription_iap.expires_date - timezone.now()).total_seconds()
        deadline_minutes = deadline_seconds / 60
        print('deadline_minutes')
        print(deadline_minutes)
        if deadline_minutes <= within_minutes:
            # verify receipt
            verify_receipt_when_update(subscription_iap)
