# app.py
import streamlit as st
from auth import register, login, get_profile

st.title("Client Portal")

# Show register or login form if not logged in
if "user" not in st.session_state:
    action = st.radio("Choose action", ["Register", "Login"])
    if action == "Register":
        register()
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
