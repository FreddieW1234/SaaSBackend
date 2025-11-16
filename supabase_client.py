import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables."
    )


@lru_cache
def get_supabase() -> Client:
    """
    Returns a cached Supabase client instance using service role key.
    """

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


