import streamlit as st
from supabase_client import get_supabase

def login():
    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        supabase = get_supabase()
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if res.user:
            st.session_state["user"] = res.user
            st.rerun()
        else:
            st.error("Login failed")

def get_profile():
    supabase = get_supabase()
    user = st.session_state.get("user")

    if not user:
        return None

    res = supabase.table("profiles") \
        .select("*") \
        .eq("id", user.id) \
        .single() \
        .execute()

    return res.data
