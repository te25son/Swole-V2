from edgedb import Client, create_client

from ..settings import get_settings


def get_client() -> Client:
    return create_client(dsn=get_settings().EDGEDB_DSN)
