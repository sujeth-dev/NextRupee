from functools import lru_cache

from app.config import settings
from app.storage.base import Storage
from app.storage.null import NullStorage
from app.storage.supabase import SupabaseStorage


@lru_cache(maxsize=1)
def get_storage() -> Storage:
    """Process-wide storage singleton: Supabase when configured, else in-memory (D-006)."""
    if settings.supabase_url and settings.supabase_service_key:
        return SupabaseStorage(settings.supabase_url, settings.supabase_service_key)
    return NullStorage()


__all__ = ["Storage", "NullStorage", "SupabaseStorage", "get_storage"]
