import streamlit as st
from auth import login, get_profile
import agency
import client

st.set_page_config(page_title="Client Portal", layout="wide")

if "user" not in st.session_state:
    login()
    st.stop()

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
