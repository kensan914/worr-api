from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from account.models import Plan, Iap, IapStatus
import requests
from account.serializers import MeSerializer
from fullfii import create_iap, update_iap
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
    }
    if receipt_data['status'] == 21006:  # この領収書は有効だが、サブスクリプションの有効期限が切れている
        additional_receipt_data = {
            'bundle_id': '',
            'original_transaction_id': res_json['latest_expired_receipt_info']['original_transaction_id'],
            'transaction_id': res_json['latest_expired_receipt_info']['transaction_id'],
            'latest_receipt': '',
            'expires_date': res_json['latest_expired_receipt_info']['expires_date_formatted'],
            'is_in_billing_retry_period': res_json['is_in_billing_retry_period'],
            'auto_renew_status': res_json['auto_renew_status'],
        }
    else:
        # bundle_id
        if 'bid' in res_json['receipt']:
            bundle_id = res_json['receipt']['bid']
        elif 'bundle_id' in res_json['receipt']:
            bundle_id = res_json['receipt']['bundle_id']
        else:
            bundle_id = ''
        # latest_receipt_info
        latest_receipt_info = res_json['latest_receipt_info'] if isinstance(res_json['latest_receipt_info'], dict) else res_json['latest_receipt_info'][0]

        def get_pending_renewal_info_param(key):
            if 'pending_renewal_info' in res_json:
                if key in res_json['pending_renewal_info']:
                    return res_json['pending_renewal_info'][key]
                elif key in res_json['pending_renewal_info'][0]:
                    return res_json['pending_renewal_info'][0][key]
            if key in latest_receipt_info:
                return latest_receipt_info[key]
            return '-1'

        is_in_billing_retry_period = get_pending_renewal_info_param('is_in_billing_retry_period')
        auto_renew_status = get_pending_renewal_info_param('auto_renew_status')

        additional_receipt_data = {
            'bundle_id': bundle_id,
            'original_transaction_id': latest_receipt_info['original_transaction_id'],
            'transaction_id': latest_receipt_info['transaction_id'],
            'latest_receipt': res_json['latest_receipt'],
            'expires_date': latest_receipt_info['expires_date'],
            'is_in_billing_retry_period': is_in_billing_retry_period,
            'auto_renew_status': auto_renew_status,
        }
    receipt_data.update(additional_receipt_data)
    return receipt_data


def verify_receipt_at_first(product_id, receipt, user, is_restore=False):
    if is_restore:
        base_error_message = '購入の復元に失敗しました。'
    else:
        base_error_message = '購入に失敗しました。'

    if not product_id in Plan.values:
        return Response({'type': 'not_found_plan', 'message': '{}不正なプランです。'.format(base_error_message)}, status=status.HTTP_404_NOT_FOUND)

    res_json = request_post_receipt(receipt)
    receipt_data = format_verify_receipt_json(res_json)

    if receipt_data['status'] != 0:
        print(1)
        return Response({'type': 'bad_status', 'message': '{}しばらく時間をおいて再度プランの変更を行ってください。'.format(base_error_message)}, status=status.HTTP_409_CONFLICT)
    if receipt_data['bundle_id'] != BUNDLE_ID:
        print(2)
        return Response({'type': 'conflict_bundle_id', 'message': '{}不正なバンドルIDです。'.format(base_error_message)}, status=status.HTTP_409_CONFLICT)

    if Iap.objects.filter(transaction_id=receipt_data['transaction_id']).exists() and not is_restore:
        print(3)
        return Response({'type': 'conflict_transaction_id', 'message': '{}'.format(base_error_message)},
                        status=status.HTTP_409_CONFLICT)

    # 有効期限が過ぎている場合
    if (timezone.now() - cvt_tz_str_to_datetime(receipt_data['expires_date'])).total_seconds() > 0:
        print(4)
        return Response({'type': 'expired', 'message': '{}更新の有効期限が切れています。新たにプランを購入してください。'.format(base_error_message)},
                        status=status.HTTP_409_CONFLICT)

    if Iap.objects.filter(original_transaction_id=receipt_data['original_transaction_id']).exists():
        iap = Iap.objects.filter(original_transaction_id=receipt_data['original_transaction_id']).first()
        if iap.status == IapStatus.SUBSCRIPTION:
            # 購入の復元
            if is_restore:
                print('購入の復元')
                print(iap.user.plan)
                iap.user.plan = Plan.FREE
                iap.user.save()
                update_iap(
                    iap=iap,
                    original_transaction_id=receipt_data['original_transaction_id'],
                    transaction_id=receipt_data['transaction_id'],
                    user=user,
                    receipt=receipt_data['latest_receipt'],
                    expires_date=cvt_tz_str_to_datetime(receipt_data['expires_date']),
                )
            else:
                print(5)
                return Response({'type': 'conflict_original_transaction_id', 'message': '{}既に購入済みの自動購読があります。購入を復元して下さい。'.format(base_error_message)},
                            status=status.HTTP_409_CONFLICT)
        else:  # 購読中のサブスクリプションの期限が切れた後にサブスクリプションを再購読
            print('再講読')
            print(iap.user.plan)
            iap.user.plan = Plan.FREE
            iap.user.save()
            update_iap(
                iap=iap,
                original_transaction_id=receipt_data['original_transaction_id'] if is_restore else None,
                transaction_id=receipt_data['transaction_id'],
                user=user,
                receipt=receipt_data['latest_receipt'],
                expires_date = cvt_tz_str_to_datetime(receipt_data['expires_date']),
                status=IapStatus.SUBSCRIPTION,
            )
    else:
        if receipt_data['latest_receipt']:
            create_iap(
                original_transaction_id=receipt_data['original_transaction_id'],
                transaction_id=receipt_data['transaction_id'],
                user=user,
                receipt=receipt_data['latest_receipt'],
                expires_date=cvt_tz_str_to_datetime(receipt_data['expires_date']),
            )
        else:
            return Response({'type': 'conflict_transaction_id', 'message': '{}'.format(base_error_message)},
                            status=status.HTTP_409_CONFLICT)

    user.plan = product_id
    user.save()
    return Response({'status': 'success', 'profile': MeSerializer(user).data}, status=status.HTTP_200_OK)


def verify_receipt_when_update(verified_iap):
    res_json = request_post_receipt(verified_iap.receipt)
    print(res_json)
    print('rrrr')

    if res_json['status'] != 0 and res_json['status'] != 21006:
        return
    receipt_data = format_verify_receipt_json(res_json)

    # case 1. 自動更新に成功している
    if not Iap.objects.filter(transaction_id=receipt_data['transaction_id']).exists():
        update_iap(
            iap=verified_iap,
            transaction_id=receipt_data['transaction_id'],
            receipt=receipt_data['latest_receipt'],
            expires_date=cvt_tz_str_to_datetime(receipt_data['expires_date']),
        )

    # case 2. まだ更新に成功していないが、今後成功する可能性がある
    elif receipt_data['is_in_billing_retry_period'] == '1':
        if verified_iap.status != IapStatus.FAILURE:
            update_iap(
                iap=verified_iap,
                receipt=receipt_data['latest_receipt'],
                status=IapStatus.FAILURE,
            )
        else:  # 自動更新失敗状態で期限が切れた
            update_iap(
                iap=verified_iap,
                receipt=receipt_data['latest_receipt'],
                status=IapStatus.EXPIRED,
            )
            verified_iap.user.plan = Plan.FREE
            verified_iap.user.save()

    # case 3. その購読は自動更新されない
    elif receipt_data['is_in_billing_retry_period'] == '0' or receipt_data['auto_renew_status'] == '0' or receipt_data['status'] == 21006:
        update_iap(
            iap=verified_iap,
            status=IapStatus.EXPIRED,
        )
        verified_iap.user.plan = Plan.FREE
        verified_iap.user.save()


def manage_iap_expires_date(within_minutes=720):
    subscription_iaps = Iap.objects.filter(status=IapStatus.SUBSCRIPTION)
    for subscription_iap in subscription_iaps:
        deadline_seconds = (subscription_iap.expires_date - timezone.now()).total_seconds()
        deadline_minutes = deadline_seconds / 60
        if deadline_minutes <= within_minutes:
            # verify receipt
            verify_receipt_when_update(subscription_iap)

    failure_iaps = Iap.objects.filter(status=IapStatus.FAILURE)
    for failure_iap in failure_iaps:
        elapsed_seconds = (timezone.now() - failure_iap.expires_date).total_seconds()
        elapsed_minutes = elapsed_seconds / 60

        if elapsed_minutes > 0:
            # verify receipt
            verify_receipt_when_update(failure_iap)
