import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Supabase Client Initialization
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

st.title("💰 Personal Expense Tracker")

# Sidebar - Expense Entry Form
st.sidebar.header("Add New Expense")
date = st.sidebar.date_input("Date")
category = st.sidebar.selectbox("Category", ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Other"])
amount = st.sidebar.number_input("Amount (Tk)", min_value=0.0, format="%.2f")
description = st.sidebar.text_input("Description")

if st.sidebar.button("Save Expense"):
    if amount > 0:
        data = {
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

# Main Page - View Data
st.header("Expense History")

try:
    response = supabase.table("expenses").select("*").order("date", desc=True).execute()
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
