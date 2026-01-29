# app.py
import streamlit as st
from auth import register, login, get_profile, complete_profile
from supabase_client import get_supabase, get_supabase_service
from datetime import datetime
import pandas as pd
import hashlib

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
if profile["role"] == "agency" and profile.get("agency_id") is None:
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

            agency_id = res.data[0]["id"]

            # Update profile with agency_id
            supabase_service.table("profiles").update({
                "agency_id": agency_id
            }).eq("id", user.id).execute()

            st.session_state["profile"] = None
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to create agency: {e}")
    st.stop()

# =====================================================
# HARD GUARD
# =====================================================
if profile["role"] == "agency" and not profile.get("agency_id"):
    st.warning("Please create your agency first before adding clients.")
    st.stop()

if not profile.get("agency_id"):
    st.error("Agency not set")
    st.stop()

# =====================================================
# Load Clients for Sidebar
# =====================================================
selected_client_id = None
clients_list = []
if profile["role"] == "agency":
    try:
        res_clients = supabase.table("clients_manager").select("*") \
            .eq("agency_id", profile["agency_id"]).order("name").execute()
        clients_list = res_clients.data or []
    except Exception as e:
        st.error(f"Failed to load clients: {e}")

    if clients_list:
        client_options = {c['name']: c['id'] for c in clients_list}
        selected_client_name = st.sidebar.selectbox("Select Client", list(client_options.keys()))
        selected_client_id = client_options.get(selected_client_name)
    else:
        st.sidebar.info("No clients yet. Add clients in 'Clients Manager' tab.")

# =====================================================
# DASHBOARD TABS
# =====================================================
tabs = st.tabs(["Clients Manager", "Planning", "Messages", "Budget", "Invoices"])

# =====================================================
# CLIENTS MANAGER TAB
# =====================================================
if profile["role"] == "agency":
    with tabs[0]:
        st.header("Clients Manager")

        # -------- Create New Client --------
        with st.form("create_client"):
            st.subheader("Add New Client")
            client_name = st.text_input("Name")
            client_email = st.text_input("Email")
            client_phone = st.text_input("Phone")
            client_address = st.text_input("Address")
            client_password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Create Client")

        if submit:
            if not client_name or not client_email or not client_password:
                st.warning("Name, email, and password are required")
            else:
                try:
                    # Use hashlib for password hashing (works without extra packages)
                    password_hash = hashlib.sha256(client_password.encode()).hexdigest()

                    # Insert into clients_manager
                    res_manager = supabase.table("clients_manager").insert({
                        "agency_id": profile["agency_id"],
                        "name": client_name,
                        "email": client_email,
                        "phone": client_phone,
                        "address": client_address,
                        "password_hash": password_hash
                    }).execute()

                    # Insert into clients table
                    client_id = res_manager.data[0]["id"]
                    supabase.table("clients").insert({
                        "id": client_id,
                        "agency_id": profile["agency_id"],
                        "name": client_name,
                        "email": client_email,
                        "phone": client_phone,
                        "address": client_address,
                        "password_hash": password_hash
                    }).execute()

                    st.success(f"Client {client_name} created successfully!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to create client: {e}")

        # -------- Display & Update Clients --------
        st.subheader("Existing Clients")
        for c in clients_list:
            with st.expander(f"{c['name']} - {c['email']}"):
                st.write(f"Address: {c.get('address','')}")
                st.write(f"Phone: {c.get('phone','')}")
                st.write(f"Created: {c['created_at']}")

                new_name = st.text_input("Name", c['name'], key=f"name-{c['id']}")
                new_email = st.text_input("Email", c['email'], key=f"email-{c['id']}")
                new_phone = st.text_input("Phone", c.get('phone',''), key=f"phone-{c['id']}")
                new_address = st.text_input("Address", c.get('address',''), key=f"address-{c['id']}")
                new_password = st.text_input("New Password", type="password", key=f"pw-{c['id']}")

                if st.button("Save Changes", key=f"save-{c['id']}"):
                    try:
                        updates = {
                            "name": new_name,
                            "email": new_email,
                            "phone": new_phone,
                            "address": new_address
                        }
                        if new_password:
                            updates["password_hash"] = hashlib.sha256(new_password.encode()).hexdigest()

                        # Update both tables
                        supabase.table("clients_manager").update(updates).eq("id", c['id']).execute()
                        supabase.table("clients").update(updates).eq("id", c['id']).execute()

                        st.success(f"Client {new_name} updated successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to update client: {e}")

# =====================================================
# PLANNING TAB
# =====================================================
with tabs[1]:
    st.header("Planning")

    if profile["role"] == "agency" and not selected_client_id:
        st.info("Select a client in the sidebar to view/add planning.")
    elif not selected_client_id:
        st.info("No client assigned yet.")
    else:
        # ---------------- ADD PLANNING ----------------
        if profile["role"] == "agency":
            st.subheader("Add planning")
            with st.form("add_planning"):
                title = st.text_input("Title")
                description = st.text_area("Description")
                due_date = st.date_input("Due date")
                submit = st.form_submit_button("Add")

            if submit:
                if not title or not due_date:
                    st.warning("Title and due date are required")
                else:
                    try:
                        res = supabase.table("planning").insert({
                            "agency_id": profile["agency_id"],
                            "client_id": selected_client_id,
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

        # ---------------- LOAD PLANNING ----------------
        try:
            planning = supabase.table("planning").select("*") \
                .eq("agency_id", profile["agency_id"]) \
                .eq("client_id", selected_client_id) \
                .order("due_date").execute()
        except Exception as e:
            st.error(f"Failed to load planning: {e}")
            planning = None

        if not planning or not planning.data:
            st.info("No planning yet")
        else:
            planning_df = pd.DataFrame(planning.data)
            planning_df['due_date'] = pd.to_datetime(planning_df['due_date'])
            total_tasks = len(planning_df)
            done_tasks = len(planning_df[planning_df['status'] == "done"])

            st.subheader("Progress")
            st.progress(done_tasks / total_tasks)
            st.caption(f"{done_tasks} of {total_tasks} tasks completed")

            for _, p in planning_df.iterrows():
                bg_color = "#d4edda" if p["status"] == "done" else "#fff3cd"
                with st.container():
                    st.markdown(f"""
                    <div style="background-color:{bg_color}; padding:15px; border-radius:8px; margin-bottom:10px;">
                        <h4>{p['title']}</h4>
                        <small>Due: {p['due_date'].strftime('%Y-%m-%d')} | Status: {p['status']}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("Details"):
                        st.write(p["description"])

                    if profile["role"] == "agency":
                        col1, col2, col3 = st.columns([3,1,1])
                        with col2:
                            if st.button("✅" if p["status"]=="todo" else "↩️", key=f"toggle-{p['id']}"):
                                try:
                                    supabase.table("planning").update({
                                        "status": "done" if p["status"]=="todo" else "todo"
                                    }).eq("id", p["id"]).eq("agency_id", profile["agency_id"]).execute()
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Failed to toggle status: {e}")
                        with col3:
                            with st.form(f"edit-{p['id']}"):
                                new_title = st.text_input("Title", p["title"])
                                new_desc = st.text_area("Description", p["description"])
                                new_due = st.date_input("Due date", p["due_date"])
                                save = st.form_submit_button("Save")
                                if save:
                                    try:
                                        supabase.table("planning").update({
                                            "title": new_title,
                                            "description": new_desc,
                                            "due_date": new_due.isoformat()
                                        }).eq("id", p["id"]).eq("agency_id", profile["agency_id"]).execute()
                                        st.success("Planning updated!")
                                        st.experimental_rerun()
                                    except Exception as e:
                                        st.error(f"Failed to update planning: {e}")

                            if st.button("Delete", key=f"delete-{p['id']}"):
                                try:
                                    supabase.table("planning").delete() \
                                        .eq("id", p["id"]).eq("agency_id", profile["agency_id"]).execute()
                                    st.success("Planning deleted!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Failed to delete planning: {e}")

# =====================================================
# MESSAGES, BUDGET, INVOICES
# =====================================================
with tabs[2]:
    st.info("Messages coming soon. Filtered per selected client.")

with tabs[3]:
    st.info("Budget coming soon. Filtered per selected client.")

with tabs[4]:
    st.info("Invoices coming soon. Filtered per selected client.")
