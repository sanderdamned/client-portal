# app.py
import streamlit as st
from auth import register, login, get_profile, complete_profile
from supabase_client import get_supabase, get_supabase_service

st.set_page_config(page_title="Client Portal")
st.title("Client Portal")

# ------------------------------------
# AUTH
# ------------------------------------
if "user" not in st.session_state:
    action = st.radio("Choose action", ["Register", "Login"])
    register() if action == "Register" else login()
    st.stop()

supabase = get_supabase()
supabase_service = get_supabase_service()
user = st.session_state["user"]

# ------------------------------------
# PROFILE
# ------------------------------------
if "profile" not in st.session_state or st.session_state.get("profile_updated"):
    st.session_state["profile"] = get_profile()
    st.session_state["profile_updated"] = False

profile = st.session_state["profile"]
if not profile:
    st.error("Profile not found")
    st.stop()

# ------------------------------------
# PROFILE SETUP
# ------------------------------------
if profile["role"] is None:
    st.subheader("Complete your profile")
    role = st.selectbox("I am a", ["agency", "client"])
    agency_id = st.text_input("Agency ID") if role == "client" else None

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

        supabase_service.table("profiles").update({
            "agency_id": res.data[0]["id"]
        }).eq("id", user.id).execute()

        st.session_state["profile_updated"] = True
        st.experimental_rerun()
    st.stop()

# ------------------------------------
# DASHBOARD
# ------------------------------------
st.success(f"Welcome {profile['role']}!")
tabs = st.tabs(["Projects", "Messages", "Budget", "Invoices"])

# ==============================
# TAB 1: PROJECTS & TASKS
# ==============================
with tabs[0]:
    st.header("Projects")

    # -------- Projects --------
    if profile["role"] == "agency":
        with st.form("add_project"):
            st.subheader("Create project")
            name = st.text_input("Project name")
            description = st.text_area("Description")
            create_project = st.form_submit_button("Create project")

        if create_project:
            supabase.table("projects").insert({
                "agency_id": profile["agency_id"],
                "name": name,
                "description": description
            }).execute()
            st.experimental_rerun()

    projects = (
        supabase
        .table("projects")
        .select("*")
        .eq("agency_id", profile["agency_id"])
        .execute()
    ).data

    if not projects:
        st.info("No projects yet")
        st.stop()

    project_map = {p["name"]: p for p in projects}
    project_name = st.selectbox("Select project", project_map.keys())
    project = project_map[project_name]

    st.divider()

    # -------- Tasks --------
    st.subheader("Tasks")

    if profile["role"] == "agency":
        with st.form("add_task"):
            title = st.text_input("Task title")
            description = st.text_area("Task description")
            due_date = st.date_input("Due date")
            submit_task = st.form_submit_button("Add task")

        if submit_task:
            supabase.table("planning").insert({
                "agency_id": profile["agency_id"],
                "project_id": project["id"],
                "title": title,
                "description": description,
                "due_date": due_date.isoformat(),
                "status": "todo"
            }).execute()
            st.experimental_rerun()

    tasks = (
        supabase
        .table("planning")
        .select("*")
        .eq("project_id", project["id"])
        .order("due_date")
        .execute()
    ).data

    for task in tasks:
        col1, col2, col3 = st.columns([4, 2, 2])

        with col1:
            st.markdown(f"**{task['title']}**")
            st.caption(task["description"])

        with col2:
            new_status = st.selectbox(
                "Status",
                ["todo", "done"],
                index=0 if task["status"] == "todo" else 1,
                key=f"status_{task['id']}"
            )
            if new_status != task["status"]:
                supabase.table("planning").update({
                    "status": new_status
                }).eq("id", task["id"]).execute()
                st.experimental_rerun()

        with col3:
            if profile["role"] == "agency":
                if st.button("🗑 Delete", key=f"del_{task['id']}"):
                    supabase.table("planning").delete().eq("id", task["id"]).execute()
                    st.experimental_rerun()

        st.divider()

# ==============================
# OTHER TABS (PLACEHOLDERS)
# ==============================
with tabs[1]:
    st.header("Messages")
    st.info("Coming next")

with tabs[2]:
    st.header("Budget")
    st.info("Coming next")

with tabs[3]:
    st.header("Invoices")
    st.info("Coming next")
