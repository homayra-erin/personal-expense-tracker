import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Initialize Supabase Client
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

st.title("🔒 Personal Expense Tracker")

# Session State for Managing Login
if "user" not in st.session_state:
    st.session_state.user = None

# Authentication Sidebar (Login / Sign Up)
if not st.session_state.user:
    st.sidebar.header("🔑 Authentication")
    auth_mode = st.sidebar.radio("Choose Action", ["Login", "Sign Up"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if auth_mode == "Sign Up":
        if st.sidebar.button("Create Account"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.sidebar.success("Account created successfully! You can now log in.")
            except Exception as e:
                st.sidebar.error(f"Sign up failed: {e}")

    elif auth_mode == "Login":
        if st.sidebar.button("Log In"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.sidebar.success("Logged in successfully!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Login failed: Check email and password.")

else:
    # User Profile Info & Logout
    st.sidebar.write(f"Logged in as: **{st.session_state.user.email}**")
    if st.sidebar.button("Log Out"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.header("Add New Expense")
    
    date = st.sidebar.date_input("Date")
    category = st.sidebar.selectbox("Category", ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Other"])
    amount = st.sidebar.number_input("Amount (Tk)", min_value=0.0, format="%.2f")
    description = st.sidebar.text_input("Description")

    if st.sidebar.button("Save Expense"):
        if amount > 0:
            data = {
                "user_id": st.session_state.user.id,
                "date": str(date),
                "category": category,
                "amount": amount,
                "description": description
            }
            try:
                supabase.table("expenses").insert(data).execute()
                st.sidebar.success("Expense saved successfully! ✅")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error saving expense: {e}")
        else:
            st.sidebar.error("Please enter an amount greater than 0.")

    # Main Dashboard
    st.header("My Expenses History")

    try:
        response = supabase.table("expenses").select("*").eq("user_id", st.session_state.user.id).order("date", desc=True).execute()
        expenses_data = response.data

        if expenses_data:
            df = pd.DataFrame(expenses_data)
            df = df[["date", "category", "amount", "description"]]
            
            st.dataframe(df, use_container_width=True)
            
            total_spent = df["amount"].sum()
            st.metric("Total Spent", f"{total_spent:,.2f} Tk")
        else:
            st.info("No expenses recorded yet.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
