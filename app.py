# app.py
import streamlit as st
from auth import register, login, get_profile, complete_profile
from supabase_client import get_supabase

st.title("Client Portal")

# ------------------------------------
# NOT LOGGED IN
# ------------------------------------
if "user" not in st.session_state:
    action = st.radio("Choose action", ["Register", "Login"])

    if action == "Register":
        register()
    else:
        login()

# ------------------------------------
# LOGGED IN
# ------------------------------------
else:
    supabase = get_supabase()
    user = st.session_state["user"]
    profile = get_profile()

    if not profile:
        st.error("Profile not found.")
        st.stop()

  # --------------------------------
# PROFILE COMPLETION (ROLE)
# --------------------------------
if profile["role"] is None:
    st.subheader("Complete your profile")

    role = st.selectbox("I am a", ["agency", "client"])
    agency_id = None

    if role == "client":
        agency_id = st.text_input("Agency ID")

    if st.button("Save profile"):
        complete_profile(role, agency_id)

        # Force reload of profile after saving
        st.session_state["profile_updated"] = True
        st.experimental_rerun()

# --------------------------------
# AGENCY CREATION
# --------------------------------
elif profile["role"] == "agency" and profile["agency_id"] is None:
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

        # Force reload of profile
        st.session_state["profile_updated"] = True
        st.experimental_rerun()


    # --------------------------------
    # DASHBOARDS
    # --------------------------------
    else:
        st.success(f"Welcome {profile['role']}!")

        if profile["role"] == "agency":
            st.header("Agency dashboard")
            st.write("Planning, messages, budget, invoices")

        else:
            st.header("Client dashboard")
            st.write("View planning, messages, budget, invoices")
