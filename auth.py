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
        supabase_auth = get_supabase()             # For sign_up and sign_in
        supabase_service = get_supabase_service()  # For inserting profile

        try:
            # 1️⃣ Create Auth user
            res_signup = supabase_auth.auth.sign_up({"email": email, "password": password})
            user = res_signup.user

            if user:
                # 2️⃣ Sign in immediately to ensure user exists in auth.users
                res_login = supabase_auth.auth.sign_in_with_password({"email": email, "password": password})
                user = res_login.user

                # 3️⃣ Insert profile using service_role (bypasses RLS)
                profile_data = {
                    "id": user.id,
                    "role": role,
                    "agency_id": agency_id if agency_id else None
                }
                supabase_service.table("profiles").insert(profile_data).execute()

                st.success("User registered! You can now log in.")
            else:
                st.error("Registration failed. Could not create user.")

        except Exception as e:
            st.error(f"Registration error: {e}")
            import traceback
            st.text(traceback.format_exc())


def login():
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pw")

    if st.button("Login"):
        supabase = get_supabase()
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if res.user:
                st.session_state["user"] = res.user
                st.success("Logged in!")
                st.experimental_rerun()
            else:
                st.error("Login failed. Check your email and password.")
        except Exception as e:
            st.error(f"Login error: {e}")
            import traceback
            st.text(traceback.format_exc())


def get_profile():
    supabase = get_supabase()
    user = st.session_state.get("user")
    if not user:
        return None
    try:
        profile = supabase.table("profiles").select("*").eq("id", user.id).single().execute()
        return profile.data
    except Exception as e:
        st.error(f"Get profile error: {e}")
        import traceback
        st.text(traceback.format_exc())
        return None
