import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from supabase import create_client, Client

# Streamlit Page Config
st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰", layout="centered")

# Supabase Initialization
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Session State for User Authentication
if "user" not in st.session_state:
    st.session_state.user = None

# --- AUTHENTICATION SECTION ---
if st.session_state.user is None:
    st.title("🔑 Expense Tracker - Login")
    
    auth_action = st.radio("Choose Action", ["Login", "Sign Up"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if auth_action == "Login":
        if st.button("Log In", type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("Successfully logged in!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    elif auth_action == "Sign Up":
        if st.button("Create Account", type="primary"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("Account created successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Sign up failed: {e}")

# --- MAIN APP SECTION (LOGGED IN) ---
else:
    user_id = st.session_state.user.id
    user_email = st.session_state.user.email

    # Header & Logout
    col_title, col_logout = st.columns([3, 1])
    with col_title:
        st.title("💰 Expense Tracker")
        st.caption(f"Logged in as: **{user_email}**")
    with col_logout:
        st.write("")
        if st.button("Log Out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.divider()

    # --- ADD NEW EXPENSE ---
    st.subheader("➕ Add New Expense")
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            exp_date = st.date_input("Date", value=date.today())
            category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Other"])
        with col2:
            description = st.text_input("Description", placeholder="e.g. Lunch at restaurant")
            amount = st.number_input("Amount ($)", min_value=0.01, step=1.0)
            
        submitted = st.form_submit_button("Add Expense", use_container_width=True)
        
        if submitted:
            data = {
                "user_id": user_id,
                "date": str(exp_date),
                "category": category,
                "description": description,
                "amount": amount
            }
            try:
                supabase.table("expenses").insert(data).execute()
                st.success("Expense added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add expense: {e}")

    st.divider()

    # --- FETCH EXPENSES ---
    try:
        response = supabase.table("expenses") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
        
        expenses_data = response.data

        if expenses_data:
            df = pd.DataFrame(expenses_data)
            df['date'] = pd.to_datetime(df['date']).dt.date

            # --- DAILY TRACKING METRICS ---
            today_date = date.today()
            today_expense = df[df['date'] == today_date]['amount'].sum()
            total_expense = df['amount'].sum()

            m1, m2 = st.columns(2)
            m1.metric(label="📅 Today's Total Expense", value=f"${today_expense:,.2f}")
            m2.metric(label="📊 Overall Total Expense", value=f"${total_expense:,.2f}")

            st.divider()

            # --- DAILY EXPENSE GRAPH ---
            st.subheader("📈 Daily Expense Trend")
            
            # Group data by date to get daily totals
            daily_df = df.groupby('date', as_index=False)['amount'].sum().sort_values('date')

            fig = px.bar(
                daily_df, 
                x='date', 
                y='amount', 
                labels={'date': 'Date', 'amount': 'Total Amount ($)'},
                title="Daily Expenses Breakdown",
                text_auto='.2f'
            )
            fig.update_traces(marker_color='#FF4B4B', textposition='outside')
            fig.update_layout(xaxis_title="", yaxis_title="Amount ($)", hovermode="x")
            
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # --- EXPENSE HISTORY TABLE ---
            st.subheader("📊 Expense History")

            # Table Headers
            h1, h2, h3, h4, h5 = st.columns([2, 2, 3, 2, 1])
            h1.markdown("**Date**")
            h2.markdown("**Category**")
            h3.markdown("**Description**")
            h4.markdown("**Amount**")
            h5.markdown("**Action**")
            st.divider()

            # Rows with Delete Option
            for item in expenses_data:
                col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 2, 1])
                col1.write(str(item["date"]))
                col2.write(item["category"])
                col3.write(item.get("description") or "-")
                col4.write(f"${item['amount']:,.2f}")
                
                # Delete Button
                if col5.button("❌", key=f"del_{item['id']}"):
                    try:
                        supabase.table("expenses").delete().eq("id", item["id"]).execute()
                        st.toast("Expense deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not delete item: {e}")
        else:
            st.info("No expense records found. Add your first expense above!")

    except Exception as e:
        st.error(f"Error loading expenses: {e}")
