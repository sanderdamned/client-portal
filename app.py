import streamlit as st
from supabase_client import get_supabase

def login():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pw")

    if st.button("Login"):
        supabase = get_supabase()
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if res.user:
            st.session_state["user"] = res.user
            st.success("Logged in")
            st.rerun()
        else:
            st.error("Login failed")

def register():
    st.subheader("Register")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pw")
    role = st.selectbox("Role", ["agency", "client"])
    agency_id = st.text_input("Agency ID (if client)", "")

    if st.button("Register"):
        supabase = get_supabase()
        # 1️⃣ Create Auth user
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        user = res.user

        if user:
            # 2️⃣ Insert into profiles table
            profile_data = {
                "id": user.id,
                "role": role,
                "agency_id": agency_id if agency_id else None
            }
            supabase.table("profiles").insert(profile_data).execute()
            st.success("User registered! You can now log in.")
        else:
            st.error("Registration failed")

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
