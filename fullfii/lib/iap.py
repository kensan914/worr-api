from rest_framework import status
from rest_framework.response import Response
from account.models import Plan, Iap
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


def verify_receipt_when_purchase(product_id, receipt, user):
    if not product_id in Plan.values:
        return Response({'type': 'not_found', 'message': "not found plan"}, status=status.HTTP_404_NOT_FOUND)

    res_json = request_post_receipt(receipt)
    print(res_json)

    if res_json['status'] != 0:
        return Response({'type': 'failed_verify_receipt', 'message': "bad status"}, status=status.HTTP_409_CONFLICT)
    if res_json['receipt']['bundle_id'] != BUNDLE_ID:
        return Response({'type': 'failed_verify_receipt', 'message': "bad bundle ID"}, status=status.HTTP_409_CONFLICT)
    if Iap.objects.filter(
            original_transaction_id=res_json['latest_receipt_info'][0]['original_transaction_id']).exists():
        return Response({'type': 'failed_verify_receipt', 'message': "the original transaction ID already exists"},
                        status=status.HTTP_409_CONFLICT)
    if Iap.objects.filter(transaction_id=res_json['latest_receipt_info'][0]['transaction_id']).exists():
        return Response({'type': 'failed_verify_receipt', 'message': "the transaction ID already exists"},
                        status=status.HTTP_409_CONFLICT)

    create_iap(
        original_transaction_id=res_json['latest_receipt_info'][0]['original_transaction_id'],
        transaction_id=res_json['latest_receipt_info'][0]['transaction_id'],
        user=user,
        receipt=res_json['latest_receipt'],
        expires_date=cvt_tz_str_to_datetime(res_json['latest_receipt_info'][0]['expires_date']),
    )
    user.plan = product_id
    user.save()
    return Response({'status': 'success', 'profile': MeSerializer(user).data}, status=status.HTTP_200_OK)
