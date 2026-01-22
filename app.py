# app.py
import streamlit as st
from auth import register, login, get_profile, complete_profile
from supabase_client import get_supabase, get_supabase_service

st.set_page_config(page_title="Client Portal")
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
    supabase_service = get_supabase_service()
    user = st.session_state["user"]

    # Load or reload profile
    if "profile" not in st.session_state or st.session_state.get("profile_updated", False):
        st.session_state["profile"] = get_profile()
        st.session_state["profile_updated"] = False

    profile = st.session_state["profile"]

    if not profile:
        st.error("Profile not found.")
        st.stop()

    # --------------------------------
    # PROFILE COMPLETION
    # --------------------------------
    if profile["role"] is None:
        st.subheader("Complete your profile")

        role = st.selectbox("I am a", ["agency", "client"])
        agency_id = None
        if role == "client":
            agency_id = st.text_input("Agency ID")

        if st.button("Save profile"):
            complete_profile(role, agency_id)
            st.session_state["profile_updated"] = True
            st.experimental_rerun()

    # --------------------------------
    # AGENCY CREATION
    # --------------------------------
    elif profile["role"] == "agency" and profile["agency_id"] is None:
        st.subheader("Create your agency")

        agency_name = st.text_input("Agency name")

        if st.button("Create agency"):
            try:
                # Use service client to bypass RLS
                res = supabase_service.table("agencies").insert({
                    "name": agency_name,
                    "owner_id": user.id
                }).execute()

                agency_id = res.data[0]["id"]

                supabase_service.table("profiles").update({
                    "agency_id": agency_id
                }).eq("id", user.id).execute()

                st.success(f"Agency '{agency_name}' created!")
                st.session_state["profile_updated"] = True
                st.experimental_rerun()

            except Exception as e:
                st.error(f"Error creating agency: {e}")
                import traceback
                st.text(traceback.format_exc())

    # --------------------------------
    # DASHBOARDS
    # --------------------------------
    else:
        st.success(f"Welcome {profile['role']}!")

        # Tabs for future functionality
        tabs = st.tabs(["Planning", "Messages", "Budget", "Invoices"])

    with tabs[0]:
    st.header("Planning")
    st.write("Agency can add/update planning. Client can view.")

    # Agency: create / update planning
    if profile["role"] == "agency":
        st.subheader("Create / Update Planning")
        title = st.text_input("Title")
        description = st.text_area("Description")
        due_date = st.date_input("Due Date")

        if st.button("Submit Planning"):
            try:
                res = supabase_service.table("planning").insert({
                    "agency_id": profile["agency_id"],
                    "client_id": None,  # We'll link client later
                    "title": title,
                    "description": description,
                    "due_date": due_date
                }).execute()

                st.success("Planning added!")
            except Exception as e:
                st.error(f"Error adding planning: {e}")

    # Display planning for both roles
    st.subheader("All Planning")
    try:
        if profile["role"] == "agency":
            planning = supabase.table("planning").select("*").eq("agency_id", profile["agency_id"]).execute()
        else:
            planning = supabase.table("planning").select("*").eq("client_id", profile["id"]).execute()

        for p in planning.data:
            st.write(f"**{p['title']}**")
            st.write(f"{p['description']}")
            st.write(f"Due: {p['due_date']}")
            st.write("---")

    except Exception as e:
        st.error(f"Error loading planning: {e}")

        with tabs[1]:
            st.header("Messages")
            st.write("Agency and client can send messages and view them.")

        with tabs[2]:
            st.header("Budget")
            st.write("Agency can submit/update budget. Client can view timeline & deltas.")

        with tabs[3]:
            st.header("Invoices")
            st.write("Agency can add invoices. Client can mark as refused, scheduled, or paid.")
