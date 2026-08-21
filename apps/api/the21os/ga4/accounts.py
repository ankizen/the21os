from the21os.ga4.client import call_ga4, get_admin_client, property_path
from the21os.ga4.models import PropertyInfo


async def get_property_info(property_id: str | None = None) -> PropertyInfo:
    client = get_admin_client()
    path = property_path(property_id)

    def fetch():
        return client.get_property(name=path)

    prop = await call_ga4(fetch)
    return PropertyInfo(
        name=prop.name,
        display_name=prop.display_name,
        time_zone=prop.time_zone,
        currency_code=prop.currency_code,
    )
