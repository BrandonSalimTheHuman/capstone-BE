from database.database import supabase


def get_google_oauth_url(redirect_to: str) -> str:
    """Return the Supabase-generated Google OAuth redirect URL."""
    if supabase is None:
        raise RuntimeError("Supabase client not configured")
    response = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {"redirect_to": redirect_to},
    })
    return response.url
