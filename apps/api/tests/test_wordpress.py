import pytest

from the21os.db.models import WordPressConnection
from the21os.wordpress.client import WordPressNotConfigured, check_woo_connection, check_wp_connection


async def test_check_wp_connection_requires_credentials() -> None:
    conn = WordPressConnection(id=1)
    with pytest.raises(WordPressNotConfigured):
        await check_wp_connection(conn)


async def test_check_woo_connection_requires_credentials() -> None:
    conn = WordPressConnection(id=1)
    with pytest.raises(WordPressNotConfigured):
        await check_woo_connection(conn)
