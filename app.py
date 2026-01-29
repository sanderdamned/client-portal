# app.py
import streamlit as st
from auth import register, login, get_profile, complete_profile
from supabase_client import get_supabase, get_supabase_service

st.set_page_config(page_title="Client Portal", layout="wide")
st.title("Client Portal")

# =====================================================
# AUTH
# =====================================================
if "user" not in st.session_state:
    action = st.radio("Choose action", ["Register", "Login"])
    register() if action == "Register" else login()
    st.stop()

supabase = get_supabase()
supabase_service = get_supabase_service()
user = st.session_state["user"]

# =====================================================
# PROFILE LOAD / REFRESH
# =====================================================
if "profile" not in st.session_state or st.session_state.get("profile_updated"):
    st.session_state["profile"] = get_profile()
    st.session_state["profile_updated"] = False

profile = st.session_state["profile"]

if not profile:
    st.error("Profile not found")
    st.stop()

# =====================================================
# PROFILE COMPLETION
# =====================================================
if profile["role"] is None:
    st.subheader("Complete your profile")

    with st.form("complete_profile"):
        role = st.selectbox("I am a", ["agency", "client"])
        agency_id = st.text_input("Agency ID (clients only)")
        submit = st.form_submit_button("Save profile")

    if submit:
        complete_profile(role, agency_id if role == "client" else None)
        st.session_state["profile_updated"] = True
        st.experimental_rerun()

    st.stop()

# =====================================================
# AGENCY CREATION
# =====================================================
if profile["role"] == "agency" and profile["agency_id"] is None:
    st.subheader("Create your agency")

    with st.form("create_agency"):
        agency_name = st.text_input("Agency name")
        submit = st.form_submit_button("Create agency")

    if submit:
        try:
            res = supabase_service.table("agencies").insert({
                "name": agency_name,
                "owner_id": user.id
            }, returning="representation").execute()

            supabase_service.table("profiles").update({
                "agency_id": res.data[0]["id"]
            }).eq("id", user.id).execute()

            st.session_state["profile"] = None
            st.experimental_rerun()

        except Exception as e:
            st.error(f"Failed to create agency: {e}")

    st.stop()

# =====================================================
# HARD GUARD
# =====================================================
if not profile.get("agency_id"):
    st.error("Agency not set")
    st.stop()

# =====================================================
# DASHBOARD
# =====================================================
st.success(f"Welcome {profile['role']}!")
tabs = st.tabs(["Planning", "Messages", "Budget", "Invoices"])

# =====================================================
# PLANNING
# =====================================================
with tabs[0]:
    st.header("Planning")

    # ---------------- ADD ----------------
    if profile["role"] == "agency":
        st.subheader("Add planning")

        with st.form("add_planning"):
            title = st.text_input("Title")
            description = st.text_area("Description")
            due_date = st.date_input("Due date")
            submit = st.form_submit_button("Add")

        if submit:
            if not title:
                st.warning("Title is required")
            elif not due_date:
                st.warning("Due date is required")
            else:
                try:
                    res = supabase.table("planning").insert({
                        "agency_id": profile["agency_id"],
                        "title": title,
                        "description": description,
                        "due_date": due_date.isoformat(),
                        "status": "todo"
                    }).execute()

                    if res.data:
                        st.success("Planning added successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to add planning row.")

                except Exception as e:
                    st.error(f"Error inserting planning: {e}")

    # ---------------- LOAD ----------------
    try:
        planning = supabase.table("planning") \
            .select("*") \
            .eq("agency_id", profile["agency_id"]) \
            .order("due_date") \
            .execute()
    except Exception as e:
        st.error(f"Failed to load planning: {e}")
        planning = None

    if not planning or not planning.data:
        st.info("No planning yet")
    else:
        for p in planning.data:
            st.divider()
            st.subheader(p["title"])
            st.write(p["description"])
            st.caption(f"Due: {p['due_date']} | Status: {p['status']}")

            if profile["role"] == "agency":

                # -------- STATUS --------
                if st.button(
                    "Toggle status",
                    key=f"status-{p['id']}"
                ):
                    try:
                        supabase.table("planning").update({
                            "status": "done" if p["status"] == "todo" else "todo"
                        }).eq("id", p["id"]) \
                         .eq("agency_id", profile["agency_id"]) \
                         .execute()
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to toggle status: {e}")

                # -------- EDIT --------
                with st.form(f"edit-{p['id']}"):
                    new_title = st.text_input("Title", p["title"])
                    new_desc = st.text_area("Description", p["description"])
                    new_due = st.date_input("Due date", p["due_date"])
                    save = st.form_submit_button("Save changes")

                if save:
                    try:
                        supabase.table("planning").update({
                            "title": new_title,
                            "description": new_desc,
                            "due_date": new_due.isoformat()
                        }).eq("id", p["id"]) \
                         .eq("agency_id", profile["agency_id"]) \
                         .execute()
                        st.success("Planning updated!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to update planning: {e}")

                # -------- DELETE --------
                if st.button("Delete", key=f"delete-{p['id']}"):
                    try:
                        supabase.table("planning") \
                            .delete() \
                            .eq("id", p["id"]) \
                            .eq("agency_id", profile["agency_id"]) \
                            .execute()
                        st.success("Planning deleted!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to delete planning: {e}")

# =====================================================
# PLACEHOLDERS
# =====================================================
with tabs[1]:
    st.info("Messages coming soon")

with tabs[2]:
    st.info("Budget coming soon")

with tabs[3]:
    st.info("Invoices coming soon")
