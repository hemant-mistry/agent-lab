from supabase import Client, create_client
from app.core.config import settings

class SupabaseService:

    def __init__(self):
        if not settings.SUPABASE_URL:
            raise RuntimeError("SUPABASE_URL is not configured")

        if not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured")

        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )

supabase_service = SupabaseService()