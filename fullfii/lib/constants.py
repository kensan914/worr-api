from config import settings

### URL ###
BASE_URL = 'http://192.168.11.46:8080/' if settings.DEBUG else 'https://fullfii.com/'


### IAP ###
IAP_STORE_API_URL = 'https://buy.itunes.apple.com/verifyReceipt/'
IAP_STORE_API_URL_SANDBOX = 'https://sandbox.itunes.apple.com/verifyReceipt/'
IAP_SHARED_SECRET = '4a8a40d5ad684ac7b273f1fe641184d2'
BUNDLE_ID = 'com.fullfii.fullfii'


### static ###
USER_EMPTY_ICON_PATH = 'static/images/user_empty_icon.png'
