from supabase import create_client
import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SUPABASE_SERVICE_KEY = st.secrets["SUPABASE_SERVICE_KEY"]

# Regular client for login / queries (RLS applies)
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Service client for server-side actions (bypass RLS, e.g., register)
def get_supabase_service():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
