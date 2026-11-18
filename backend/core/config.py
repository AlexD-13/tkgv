import os
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from decouple import Config, RepositoryEnv

_BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
_PROJECT_DIR = os.path.dirname(_BACKEND_DIR)
_ENV_PATH = next(
    (
        path
        for path in (
            os.path.join(_BACKEND_DIR, '.env'),
            os.path.join(_PROJECT_DIR, '.env'),
        )
        if os.path.isfile(path)
    ),
    None,
)
config = Config(RepositoryEnv(_ENV_PATH)) if _ENV_PATH else None


def get(key: str, default: str = '') -> str:
    if config is not None:
        return config(key, default=default)
    return os.getenv(key, default)


DATABASE_URL = get('DATABASE_URL', '')
SECRET_KEY = get('SECRET_KEY', 'change-me-for-local-development')
ADMIN_TOKEN = get('ADMIN_TOKEN', 'admin')

_cors = get(
    'CORS_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000,http://192.168.1.5:3000',
)
CORS_ORIGINS = [origin.strip() for origin in _cors.split(',') if origin.strip()]


def normalize_database_url(url: str) -> str:
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    if url.startswith('postgresql://'):
        url = 'postgresql+asyncpg://' + url[len('postgresql://'):]
    return url


DATABASE_URL = normalize_database_url(DATABASE_URL)

DB_SSLMODE = get('DB_SSLMODE', '').lower()

if DATABASE_URL.startswith('postgresql+asyncpg://'):
    parsed = urlsplit(DATABASE_URL)
    query = parse_qs(parsed.query)
    query.pop('sslmode', None)
    DATABASE_URL = urlunsplit(
        parsed._replace(query=urlencode(query, doseq=True))
    )
