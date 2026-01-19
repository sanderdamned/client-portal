import streamlit as st
from supabase_client import get_supabase, get_supabase_service

def register():
    st.subheader("Register")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_pw")
    role = st.selectbox("Role", ["agency", "client"])
    agency_id = st.text_input("Agency ID (if client)", "")

    if st.button("Register"):
        supabase_auth = get_supabase()  # for sign_up
        supabase_service = get_supabase_service()  # for inserting profile

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
