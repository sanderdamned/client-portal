import streamlit as st
from auth import login, register, get_profile
import agency
import client

st.set_page_config(page_title="Client Portal", layout="wide")

option = st.sidebar.selectbox("Choose action", ["Login", "Register"])

if option == "Login":
    login()
    st.stop()
elif option == "Register":
    register()
    st.stop()

# After login
profile = get_profile()

if not profile:
    st.error("Profile not found")
    st.stop()

if profile["role"] == "agency":
    agency.render()
elif profile["role"] == "client":
    client.render()
else:
    st.error("Invalid role")
