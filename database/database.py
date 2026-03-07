import os
from supabase import create_client, Client
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

sqlalchemy_database_url = os.environ.get("https://uhsdrnhqblimzoklkffy.supabase.co")

engine = create_engine(sqlalchemy_database_url)
url: str = os.environ.get("https://uhsdrnhqblimzoklkffy.supabase.co")
key: str = os.environ.get("sb_publishable_t5GztOxHxa9Uq2T8rhdyNg_3HToEwtD")
supabase: Client = create_client(url, key)

