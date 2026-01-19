# auth.py
import streamlit as st
from supabase_client import get_supabase, get_supabase_service

def register():
    st.subheader("Register")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pw")
    role = st.selectbox("Role", ["agency", "client"])
    agency_id = st.text_input("Agency ID (if client)", "")

    if st.button("Register"):
        supabase_auth = get_supabase()           # For sign_up
        supabase_service = get_supabase_service()  # For inserting profile

        # 1️⃣ Create Auth user
        res = supabase_auth.auth.sign_up({"email": email, "password": password})
        user = res.user

        if user:
            # 2️⃣ Insert profile using service_role (bypass RLS)
            profile_data = {
                "id": user.id,
                "role": role,
                "agency_id": agency_id if agency_id else None
            }
            supabase_service.table("profiles").insert(profile_data).execute()
            st.success("User registered! You can now log in.")
        else:
            st.error("Registration failed")


def login():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pw")

    if st.button("Login"):
        supabase = get_supabase()
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state["user"] = res.user
            st.success("Logged in!")
            st.experimental_rerun()
        else:
            st.error("Login failed")


def get_profile():
    supabase = get_supabase()
    user = st.session_state.get("user")
    if not user:

        try:
    supabase_service.table("profiles").insert(profile_data).execute()
except Exception as e:
    st.error(f"Insert failed: {e}")
    import traceback
    st.text(traceback.format_exc())

        return None
    profile = supabase.table("profiles").select("*").eq("id", user.id).single().execute()
    return profile.data
