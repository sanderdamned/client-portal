# auth.py
import streamlit as st
from supabase_client import get_supabase

# -------------------
# REGISTER
# -------------------
def register():
    st.subheader("Register")

    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pw")

    if st.button("Register"):
        supabase = get_supabase()
        try:
            res = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if res.user:
                st.success("Registration successful. You can now log in.")
            else:
                st.error("Registration failed.")

        except Exception as e:
            st.error(f"Registration error: {e}")


# -------------------
# LOGIN
# -------------------
def login():
    st.subheader("Login")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pw")

    if st.button("Login"):
        supabase = get_supabase()
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if res.user:
                st.session_state["user"] = res.user
                st.success("Logged in!")
                st.experimental_rerun()
            else:
                st.error("Invalid email or password.")

        except Exception as e:
            st.error(f"Login error: {e}")


# -------------------
# GET PROFILE
# -------------------
def get_profile():
    supabase = get_supabase()
    user = st.session_state.get("user")

    if not user:
        return None

    try:
        res = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user.id)
            .single()
            .execute()
        )
        return res.data

    except Exception as e:
        st.error(f"Profile error: {e}")
        return None


# -------------------
# COMPLETE PROFILE
# -------------------
def complete_profile(role, agency_id=None):
    supabase = get_supabase()
    user = st.session_state.get("user")

    if not user:
        return

    supabase.table("profiles").update({
        "role": role,
        "agency_id": agency_id
    }).eq("id", user.id).execute()
