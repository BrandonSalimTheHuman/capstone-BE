"""Final cleanup step — run after all scrapers complete.

Sets is_available = FALSE for every store_product whose last_updated timestamp
is older than the cutoff window (default 12 hours).  Products still seen in this
scrape batch will have been refreshed to NOW() by db_upload.py and are therefore
untouched.
"""

import os
import psycopg2
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def mark_stale_unavailable(hours: int = 12) -> None:
    conn_str = os.environ.get("DATABASE_URL")
    if not conn_str:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()

    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cur.execute(
            """
            UPDATE store_products
            SET is_available = FALSE
            WHERE is_available = TRUE AND last_updated < %s
            """,
            (cutoff,),
        )
        count = cur.rowcount
        conn.commit()
        print(f"[mark_unavailable] Marked {count} record(s) as unavailable "
              f"(last_updated before {cutoff.isoformat()} UTC)")

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    mark_stale_unavailable(hours=12)
