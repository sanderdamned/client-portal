# app.py
import streamlit as st
from auth import register, login, get_profile, complete_profile
from supabase_client import get_supabase, get_supabase_service

st.set_page_config(page_title="Client Portal", layout="wide")
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

    st.stop()

# ------------------------------------
# LOGGED IN
# ------------------------------------
supabase = get_supabase()
supabase_service = get_supabase_service()
user = st.session_state["user"]

# ------------------------------------
# LOAD / REFRESH PROFILE
# ------------------------------------
if "profile" not in st.session_state or st.session_state.get("profile_updated"):
    st.session_state["profile"] = get_profile()
    st.session_state["profile_updated"] = False

profile = st.session_state["profile"]

if not profile:
    st.error("Profile not found.")
    st.stop()

# ------------------------------------
# PROFILE COMPLETION
# ------------------------------------
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

    st.stop()

# ------------------------------------
# AGENCY CREATION
# ------------------------------------
if profile["role"] == "agency" and profile["agency_id"] is None:
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

        # IMPORTANT: force profile reload
        st.session_state["profile"] = None
        st.experimental_rerun()

    st.stop()

# ------------------------------------
# HARD GUARD (RLS SAFETY)
# ------------------------------------
if not profile.get("agency_id"):
    st.error("Agency not set. Please refresh or complete setup.")
    st.stop()

# ------------------------------------
# DASHBOARD
# ------------------------------------
st.success(f"Welcome {profile['role']}!")

tabs = st.tabs(["Planning", "Messages", "Budget", "Invoices"])

# ====================================
# TAB 1: PLANNING
# ====================================
with tabs[0]:
    st.header("Planning")

    # ----------------------------
    # ADD PLANNING (AGENCY ONLY)
    # ----------------------------
    if profile["role"] == "agency":
        st.subheader("Add planning item")

        with st.form("add_planning"):
            title = st.text_input("Title")
            description = st.text_area("Description")
            due_date = st.date_input("Due date")

            clients = supabase.table("profiles") \
                .select("id,email") \
                .eq("agency_id", profile["agency_id"]) \
                .eq("role", "client") \
                .execute()

            client_map = {c["email"]: c["id"] for c in clients.data} if clients.data else {}
            client_choice = st.selectbox(
                "Assign to client (optional)",
                ["None"] + list(client_map.keys())
            )

            submitted = st.form_submit_button("Add planning")

        if submitted:
            client_id = client_map.get(client_choice) if client_choice != "None" else None

            supabase.table("planning").insert({
                "agency_id": profile["agency_id"],  # MUST NOT BE NULL
                "client_id": client_id,
                "title": title,
                "description": description,
                "due_date": due_date.isoformat(),
                "status": "todo"
            }).execute()

            st.success("Planning item added")
            st.experimental_rerun()

    # ----------------------------
    # LOAD PLANNING
    # ----------------------------
    if profile["role"] == "agency":
        planning = supabase.table("planning") \
            .select("*") \
            .eq("agency_id", profile["agency_id"]) \
            .order("due_date") \
            .execute()
    else:
        planning = supabase.table("planning") \
            .select("*") \
            .eq("agency_id", profile["agency_id"]) \
            .or_(f"client_id.eq.{profile['id']},client_id.is.null") \
            .order("due_date") \
            .execute()

    st.subheader("All planning")

    if not planning.data:
        st.info("No planning items yet.")
    else:
        for p in planning.data:
            with st.container(border=True):
                st.markdown(f"### {p['title']}")
                st.write(p["description"])
                st.caption(f"Due: {p['due_date']}")

                st.write(f"Status: **{p.get('status', 'todo')}**")

                # ----------------------------
                # AGENCY ACTIONS
                # ----------------------------
                if profile["role"] == "agency":
                    col1, col2, col3 = st.columns(3)

                    # TOGGLE STATUS
                    with col1:
                        if st.button(
                            "Mark done" if p["status"] != "done" else "Mark todo",
                            key=f"status-{p['id']}"
                        ):
                            supabase.table("planning").update({
                                "status": "done" if p["status"] != "done" else "todo"
                            }).eq("id", p["id"]).execute()
                            st.experimental_rerun()

                    # EDIT
                    with col2:
                        with st.popover("Edit"):
                            with st.form(f"edit-{p['id']}"):
                                new_title = st.text_input("Title", p["title"])
                                new_desc = st.text_area("Description", p["description"])
                                new_due = st.date_input("Due date", p["due_date"])

                                save = st.form_submit_button("Save")

                            if save:
                                supabase.table("planning").update({
                                    "title": new_title,
                                    "description": new_desc,
                                    "due_date": new_due.isoformat()
                                }).eq("id", p["id"]).execute()
                                st.experimental_rerun()

                    # DELETE
                    with col3:
                        if st.button("Delete", key=f"delete-{p['id']}"):
                            supabase.table("planning").delete().eq("id", p["id"]).execute()
                            st.experimental_rerun()

# ====================================
# TAB 2: MESSAGES
# ====================================
with tabs[1]:
    st.header("Messages")
    st.info("Messaging will be added later.")

# ====================================
# TAB 3: BUDGET
# ====================================
with tabs[2]:
    st.header("Budget")
    st.info("Budget module coming soon.")

# ====================================
# TAB 4: INVOICES
# ====================================
with tabs[3]:
    st.header("Invoices")
    st.info("Invoices module coming soon.")
