# BudgetBakers Wallet - Home Assistant Integration

Custom Home Assistant integration for Wallet by BudgetBakers.

## Features

- Installable through HACS (custom repository)
- Config flow with Bearer token input
- Fetches all transactions from the last 7 days
- Includes only active accounts (`archived=false`)
- Polling every 15 minutes
- One sensor with transaction count as state and full transaction list in attributes

## Installation (HACS)

1. Open HACS in Home Assistant.
2. Go to **Integrations**.
3. Open menu (three dots) -> **Custom repositories**.
4. Add repository URL:
   - `https://github.com/picu63/BudgetbakersHAIntegration`
   - Category: **Integration**
5. Find **BudgetBakers Wallet** in HACS and install it.
6. Restart Home Assistant.

## Configuration

1. Go to **Settings -> Devices & Services -> Add Integration**.
2. Search for **BudgetBakers Wallet**.
3. Paste your Wallet API Bearer token.

## Entity

This integration creates two sensors:

- `sensor.budgetbakers_wallet_transactions_last_7_days`
  - **state**: number of transactions from last 7 days
  - **attributes**:
    - `transactions`: list of transaction objects (up to 1000 items in attributes)
    - `account_count`: number of active accounts included
    - `active_account_ids`: list of included account IDs
    - `requests_made`: number of API requests during last refresh
    - `updated_at`: refresh timestamp
    - `last_error`: latest coordinator error (if any)

- `sensor.budgetbakers_wallet_spent_in_pln_last_7_days`
  - **state**: total amount spent in PLN in last 7 days
  - calculated from `baseAmount` for records where `recordType=expense` and `baseAmount.currencyCode=PLN`

## Notes

- API rate limits are handled by Home Assistant retry cycle.
- If token expires, re-authentication flow is available.
