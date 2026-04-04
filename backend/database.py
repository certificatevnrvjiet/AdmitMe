from __future__ import annotations

from urllib.parse import quote_plus

from config.settings import (
    DB_PROVIDER,
    SUPABASE_KEY,
    SUPABASE_URL,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DB,
    MYSQL_USER,
    MYSQL_PASSWORD,
)

if DB_PROVIDER == "mysql":
    try:
        import cryptography  # noqa: F401
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing Python dependency 'cryptography' for MySQL auth. "
            "Activate backend venv and run: pip install -r requirements.txt"
        ) from exc

    from db.mysql_adapter import MySQLClient

    encoded_user = quote_plus(MYSQL_USER or "")
    encoded_password = quote_plus(MYSQL_PASSWORD or "")
    mysql_url = f"mysql+pymysql://{encoded_user}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    supabase = MySQLClient(mysql_url)
else:
    from supabase import create_client, Client

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
