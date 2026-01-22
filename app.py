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

        # Tabs for different functionality
        tabs = st.tabs(["Planning", "Messages", "Budget", "Invoices"])

        # ----------------------------
        # TAB 1: Planning
        # ----------------------------
        with tabs[0]:
            st.header("Planning")
            st.write("Agency can add/update planning. Client can view.")

            # Agency: create / update planning
            if profile["role"] == "agency":
                st.subheader("Create / Update Planning")
                title = st.text_input("Title")
                description = st.text_area("Description")
                due_date = st.date_input("Due Date")

                # Optional: select a client for this planning
                clients = supabase.table("profiles").select("*").eq("agency_id", profile["agency_id"]).eq("role", "client").execute()
                client_options = {c["email"]: c["id"] for c in clients.data} if clients.data else {}
                client_choice = st.selectbox("Assign to client (optional)", ["None"] + list(client_options.keys()))
                client_id = client_options.get(client_choice) if client_choice != "None" else None

                if st.button("Submit Planning"):
                    try:
                        res = supabase_service.table("planning").insert({
                            "agency_id": profile["agency_id"],
                            "client_id": client_id,
                            "title": title,
                            "description": description,
                            "due_date": due_date.isoformat() if due_date else None
                        }).execute()

                        if res.data:
                            st.success("Planning added!")
                            # Clear inputs
                            title = ""
                            description = ""
                        else:
                            st.error("Planning insertion failed.")

                    except Exception as e:
                        st.error(f"Error adding planning: {e}")

            # Display planning for both roles
            st.subheader("All Planning")
            try:
                if profile["role"] == "agency":
                    planning = supabase.table("planning").select("*").eq("agency_id", profile["agency_id"]).execute()
                else:
                    # Client sees planning assigned to them or general agency planning
                    planning = supabase.table("planning").select("*").or_(
                        f"client_id.eq.{profile['id']},client_id.is.null"
                    ).execute()

                if planning.data:
                    for p in planning.data:
                        st.write(f"**{p['title']}**")
                        st.write(f"{p['description']}")
                        st.write(f"Due: {p['due_date']}")
                        st.write("---")
                else:
                    st.info("No planning found yet.")

            except Exception as e:
                st.error(f"Error loading planning: {e}")

        # ----------------------------
        # TAB 2: Messages
        # ----------------------------
        with tabs[1]:
            st.header("Messages")
            st.write("Agency and client can send messages and view them.")
            # TODO: implement messaging later

        # ----------------------------
        # TAB 3: Budget
        # ----------------------------
        with tabs[2]:
            st.header("Budget")
            st.write("Agency can submit/update budget. Client can view timeline & deltas.")
            # TODO: implement budget later

        # ----------------------------
        # TAB 4: Invoices
        # ----------------------------
        with tabs[3]:
            st.header("Invoices")
            st.write("Agency can add invoices. Client can mark as refused, scheduled, or paid.")
            # TODO: implement invoices later
