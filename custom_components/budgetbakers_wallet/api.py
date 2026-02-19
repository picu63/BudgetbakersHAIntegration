"""API client for BudgetBakers Wallet."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import ACCOUNTS_ENDPOINT, BASE_URL, DEFAULT_PAGE_LIMIT, RECORDS_ENDPOINT


class BudgetBakersApiError(Exception):
    """Base API error."""


class BudgetBakersAuthError(BudgetBakersApiError):
    """Authentication failed."""


class BudgetBakersRateLimitError(BudgetBakersApiError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


@dataclass(slots=True)
class WalletFetchResult:
    """Result of combined wallet fetch."""

    transactions: list[dict[str, Any]]
    account_count: int
    active_account_ids: list[str]
    requests_made: int


class BudgetBakersApiClient:
    """Async client for Wallet by BudgetBakers REST API."""

    def __init__(self, session: ClientSession, token: str) -> None:
        self._session = session
        self._token = token
        self._requests_made = 0

    @property
    def requests_made(self) -> int:
        """Return amount of requests made in the current fetch run."""
        return self._requests_made

    async def validate_token(self) -> None:
        """Validate token by requesting the first page of accounts."""
        await self._request_json(
            endpoint=ACCOUNTS_ENDPOINT,
            params={"limit": 1, "offset": 0},
        )

    async def get_last_week_transactions_all_active_accounts(self) -> WalletFetchResult:
        """Fetch records from all non-archived accounts for last 7 days."""
        self._requests_made = 0

        accounts = await self._fetch_accounts()
        active_accounts = [acc for acc in accounts if not bool(acc.get("archived", False))]
        active_account_ids = [acc["id"] for acc in active_accounts if acc.get("id")]

        now_utc = datetime.now(UTC)
        start_utc = now_utc - timedelta(days=7)

        all_transactions: list[dict[str, Any]] = []
        for account_id in active_account_ids:
            account_records = await self._fetch_records_for_account(
                account_id=account_id,
                start_utc=start_utc,
                end_utc=now_utc,
            )
            all_transactions.extend(account_records)

        all_transactions.sort(key=lambda item: item.get("recordDate", ""), reverse=True)

        return WalletFetchResult(
            transactions=all_transactions,
            account_count=len(active_account_ids),
            active_account_ids=active_account_ids,
            requests_made=self._requests_made,
        )

    async def _fetch_accounts(self) -> list[dict[str, Any]]:
        """Fetch all accounts using pagination."""
        accounts: list[dict[str, Any]] = []
        offset = 0

        while True:
            payload = await self._request_json(
                endpoint=ACCOUNTS_ENDPOINT,
                params={"limit": DEFAULT_PAGE_LIMIT, "offset": offset},
            )
            accounts.extend(payload.get("accounts", []))

            next_offset = payload.get("nextOffset")
            if next_offset is None:
                break
            offset = int(next_offset)

        return accounts

    async def _fetch_records_for_account(
        self,
        account_id: str,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch all records for a single account in a date range."""
        records: list[dict[str, Any]] = []
        offset = 0

        start_value = start_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        end_value = end_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")

        while True:
            params: list[tuple[str, str | int]] = [
                ("accountId", account_id),
                ("recordDate", f"gte.{start_value}"),
                ("recordDate", f"lt.{end_value}"),
                ("limit", DEFAULT_PAGE_LIMIT),
                ("offset", offset),
            ]

            payload = await self._request_json(endpoint=RECORDS_ENDPOINT, params=params)
            records.extend(payload.get("records", []))

            next_offset = payload.get("nextOffset")
            if next_offset is None:
                break
            offset = int(next_offset)

        return records

    async def _request_json(
        self,
        endpoint: str,
        params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Perform an authenticated JSON request."""
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

        url = f"{BASE_URL}{endpoint}"

        try:
            async with self._session.get(
                url,
                headers=headers,
                params=params,
                timeout=30,
            ) as response:
                self._requests_made += 1

                if response.status == 401:
                    raise BudgetBakersAuthError("Unauthorized: invalid or expired token")

                if response.status == 429:
                    retry_after_raw = response.headers.get("Retry-After")
                    retry_after = int(retry_after_raw) if retry_after_raw and retry_after_raw.isdigit() else None
                    raise BudgetBakersRateLimitError(
                        "Rate limit exceeded",
                        retry_after=retry_after,
                    )

                response.raise_for_status()
                payload = await response.json()
                if not isinstance(payload, dict):
                    raise BudgetBakersApiError("Unexpected API response format")
                return payload

        except BudgetBakersApiError:
            raise
        except ClientResponseError as err:
            raise BudgetBakersApiError(
                f"API request failed with status {err.status}"
            ) from err
        except ClientError as err:
            raise BudgetBakersApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise BudgetBakersApiError("Request timed out") from err
