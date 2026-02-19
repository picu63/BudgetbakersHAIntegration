"""Constants for the BudgetBakers Wallet integration."""

from datetime import timedelta

DOMAIN = "budgetbakers_wallet"
PLATFORMS = ["sensor"]

CONF_TOKEN = "token"

DEFAULT_NAME = "BudgetBakers Wallet"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)

BASE_URL = "https://rest.budgetbakers.com/wallet"
ACCOUNTS_ENDPOINT = "/v1/api/accounts"
RECORDS_ENDPOINT = "/v1/api/records"

DEFAULT_PAGE_LIMIT = 100
MAX_TRANSACTIONS_IN_ATTRIBUTES = 1000

ATTR_TRANSACTIONS = "transactions"
ATTR_ACCOUNT_COUNT = "account_count"
ATTR_ACTIVE_ACCOUNT_IDS = "active_account_ids"
ATTR_UPDATED_AT = "updated_at"
ATTR_REQUESTS_MADE = "requests_made"
ATTR_TOTAL_TRANSACTIONS = "total_transactions"
ATTR_LAST_ERROR = "last_error"
