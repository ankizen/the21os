from facebook_business.adobjects.adaccount import AdAccount as FbAdAccount

from the21os.meta.client import call_meta, get_account
from the21os.meta.models import AccountInfo

_FIELDS = [
    FbAdAccount.Field.id,
    FbAdAccount.Field.name,
    FbAdAccount.Field.currency,
    FbAdAccount.Field.timezone_name,
    FbAdAccount.Field.account_status,
    FbAdAccount.Field.amount_spent,
]


async def get_account_info(account_id: str | None = None) -> AccountInfo:
    account = get_account(account_id)

    def fetch() -> dict:
        account.api_get(fields=_FIELDS)
        return dict(account)

    data = await call_meta(fetch)
    return AccountInfo.model_validate(data)
