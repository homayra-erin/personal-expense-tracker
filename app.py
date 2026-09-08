import streamlit as st
import pandas as pd
from datetime import datetime
import os

FILE_NAME = "expenses.csv"

st.set_page_config(
    page_title="My Expense Tracker",
    page_icon="💰",
    layout="centered"
)

st.title("💰 My Expense Tracker")
st.write("Track your daily expenses easily!")


# Create CSV file if it does not exist
if not os.path.exists(FILE_NAME):
    empty_df = pd.DataFrame(
        columns=["Date", "Category", "Amount", "Description"]
    )
    empty_df.to_csv(FILE_NAME, index=False)


def load_data():
    return pd.read_csv(FILE_NAME)


def save_expense(date, category, amount, description):
    new_expense = pd.DataFrame(
        [[date, category, amount, description]],
        columns=["Date", "Category", "Amount", "Description"]
    )

    new_expense.to_csv(
        FILE_NAME,
        mode="a",
        header=False,
        index=False
    )


menu = st.sidebar.selectbox(
    "Menu",
    ["➕ Add Expense", "📊 Dashboard", "📋 All Expenses"]
)


# ADD EXPENSE
if menu == "➕ Add Expense":

    st.subheader("➕ Add New Expense")

    date = st.date_input(
        "Date",
        value=datetime.today()
    )

    category = st.selectbox(
        "Category",
        [
            "Food",
            "Travel",
            "Education",
            "Shopping",
            "Entertainment",
            "Other"
        ]
    )

    amount = st.number_input(
        "Amount (Tk)",
        min_value=0.0,
        step=10.0
    )

    description = st.text_input("Description")

    if st.button("💾 Save Expense"):

        if amount > 0:

            save_expense(
                date,
                category,
                amount,
                description
            )

            st.success("Expense saved successfully! ✅")

        else:
            st.warning("Please enter an amount greater than 0.")


# DASHBOARD
elif menu == "📊 Dashboard":

    st.subheader("📊 Expense Dashboard")

    df = load_data()

    if not df.empty:

        total = df["Amount"].sum()

        st.metric(
            "Total Expense",
            f"{total:,.0f} Tk"
        )

        st.subheader("Expense by Category")

        category_data = (
            df.groupby("Category")["Amount"]
            .sum()
        )

        st.bar_chart(category_data)

    else:
        st.info("No expenses added yet.")


# ALL EXPENSES
elif menu == "📋 All Expenses":

    st.subheader("📋 All Expenses")

    df = load_data()

    if not df.empty:
        st.dataframe(
            df,
            use_container_width=True
        )
    else:
        st.info("No expenses found.")

