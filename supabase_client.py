# supabase_client.py
from supabase import create_client
import streamlit as st

# Load secrets from Streamlit Cloud
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]               # anon key
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]  # service_role key

# Regular client (RLS applies)
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Service role client (bypasses RLS, used for registration)
def get_supabase_service():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
