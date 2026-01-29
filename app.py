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
    if "profile" not in st.session_state or st.session_state.get("profile_updated"):
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
            res = supabase_service.table("agencies").insert({
                "name": agency_name,
                "owner_id": user.id
            }, returning="representation").execute()

            agency_id = res.data[0]["id"]

            supabase_service.table("profiles").update({
                "agency_id": agency_id
            }).eq("id", user.id).execute()

            st.success(f"Agency '{agency_name}' created!")
            st.session_state["profile_updated"] = True
            st.experimental_rerun()

    # --------------------------------
    # DASHBOARD
    # --------------------------------
    else:
        st.success(f"Welcome {profile['role']}!")

        tabs = st.tabs(["Planning", "Messages", "Budget", "Invoices"])

        # ----------------------------
        # TAB 1: Planning
        # ----------------------------
        with tabs[0]:
            st.header("Planning")
            st.write("Agency can add planning items. Clients can view.")

            # Agency: add planning
            if profile["role"] == "agency":
                st.subheader("Add planning item")

                with st.form("add_planning"):
                    title = st.text_input("Title")
                    description = st.text_area("Description")
                    due_date = st.date_input("Due date")

                    clients = (
                        supabase
                        .table("profiles")
                        .select("id,email")
                        .eq("agency_id", profile["agency_id"])
                        .eq("role", "client")
                        .execute()
                    )

                    client_options = {c["email"]: c["id"] for c in clients.data} if clients.data else {}
                    client_choice = st.selectbox(
                        "Assign to client (optional)",
                        ["None"] + list(client_options.keys())
                    )

                    submitted = st.form_submit_button("Add planning")

                if submitted:
                    client_id = client_options.get(client_choice) if client_choice != "None" else None

                    supabase.table("planning").insert({
                        "agency_id": profile["agency_id"],
                        "client_id": client_id,
                        "title": title,
                        "description": description,
                        "due_date": due_date.isoformat(),
                        "project_name": "General"  # future-proof
                    }).execute()

                    st.success("Planning item added")
                    st.experimental_rerun()

            # Display planning (agency + client)
            st.subheader("All planning")

            if profile["role"] == "agency":
                planning = (
                    supabase
                    .table("planning")
                    .select("*")
                    .eq("agency_id", profile["agency_id"])
                    .order("due_date")
                    .execute()
                )
            else:
                planning = (
                    supabase
                    .table("planning")
                    .select("*")
                    .eq("agency_id", profile["agency_id"])
                    .or_(f"client_id.eq.{profile['id']},client_id.is.null")
                    .order("due_date")
                    .execute()
                )

            if planning.data:
                for p in planning.data:
                    st.markdown(f"### {p['title']}")
                    st.write(p["description"])
                    st.caption(f"Due: {p['due_date']}")
                    st.divider()
            else:
                st.info("No planning items yet.")

        # ----------------------------
        # TAB 2: Messages
        # ----------------------------
        with tabs[1]:
            st.header("Messages")
            st.info("Coming next")

        # ----------------------------
        # TAB 3: Budget
        # ----------------------------
        with tabs[2]:
            st.header("Budget")
            st.info("Coming next")

        # ----------------------------
        # TAB 4: Invoices
        # ----------------------------
        with tabs[3]:
            st.header("Invoices")
            st.info("Coming next")
