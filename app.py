# app.py
import streamlit as st
from auth import register, login, get_profile

st.title("Client Portal")

# Show register or login form if not logged in
if "user" not in st.session_state:
    action = st.radio("Choose action", ["Register", "Login"])
    if action == "Register":
        register()
        if profile["role"] == "agency" and profile["agency_id"] is None:
    st.subheader("Create your agency")

    agency_name = st.text_input("Agency name")

    if st.button("Create agency"):
        supabase = get_supabase()
        res = supabase.table("agencies").insert({
            "name": agency_name,
            "owner_id": user.id
        }).execute()

        agency_id = res.data[0]["id"]

        supabase.table("profiles").update({
            "agency_id": agency_id
        }).eq("id", user.id).execute()

        st.experimental_rerun()

    else:
        login()
else:
    # User is logged in
    profile = get_profile()
    if profile:
        st.write(f"Welcome {profile['role']}!")
        if profile['role'] == "agency":
            st.write("Agency dashboard goes here")
        else:
            st.write("Client dashboard goes here")
    else:
        st.error("Profile not found")
