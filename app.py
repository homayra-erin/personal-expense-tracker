import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
from supabase import create_client, Client

# Streamlit Page Config
st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰", layout="wide")

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

    # Top Header & Logout
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title("💰 Personal Expense Tracker")
        st.caption(f"Logged in as: **{user_email}**")
    with col_logout:
        st.write("")
        if st.button("Log Out", type="secondary"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    st.divider()

    # --- ADD NEW EXPENSE SECTION ---
    st.subheader("➕ Add New Expense")
    with st.form("expense_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
        with col1:
            exp_date = st.date_input("Date", value=date.today())
        with col2:
            category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"])
        with col3:
            description = st.text_input("Description", placeholder="e.g. Snacks or Bus Fare")
        with col4:
            amount = st.number_input("Amount ($)", min_value=0.01, step=1.0)
            
        submitted = st.form_submit_button("Add Expense", use_container_width=True, type="primary")
        
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
                st.toast("Expense added successfully!", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add expense: {e}")

    st.divider()

    # --- FETCH EXPENSES DATA ---
    try:
        response = supabase.table("expenses") \
            .select("*") \
            .order("date", desc=False) \
            .execute()
        
        expenses_data = response.data

        if expenses_data:
            df = pd.DataFrame(expenses_data)
            df['datetime'] = pd.to_datetime(df['date'])
            df['month'] = df['datetime'].dt.strftime('%Y-%m')

            # --- REAL-TIME SUMMARY METRICS ---
            today_str = str(date.today())
            current_month_str = date.today().strftime('%Y-%m')

            today_total = df[df['date'] == today_str]['amount'].sum()
            month_total = df[df['month'] == current_month_str]['amount'].sum()
            overall_total = df['amount'].sum()

            m1, m2, m3 = st.columns(3)
            m1.metric(label="📅 Today's Expense", value=f"${today_total:,.2f}")
            m2.metric(label="🗓️ This Month's Expense", value=f"${month_total:,.2f}")
            m3.metric(label="📊 Overall Total Expense", value=f"${overall_total:,.2f}")

            st.divider()

            # --- VISUAL ANALYTICS & CHARTS ---
            st.subheader("📈 Visual Analytics")
            tab_daily, tab_monthly, tab_category = st.tabs(["📅 Daily Track", "🗓️ 12-Month Analytics", "🏷️ Category Breakdown"])

            # 1. UPDATED DAILY TRACK TAB
            with tab_daily:
                daily_df = df.groupby('date')['amount'].sum().reset_index()
                daily_df['date'] = pd.to_datetime(daily_df['date'])
                daily_df = daily_df.sort_values('date')

                avg_daily = daily_df['amount'].mean() if not daily_df.empty else 0.0

                st.caption(f"💡 Daily Average Expense: **${avg_daily:,.2f}**")

                fig_daily = go.Figure()
                
                # DESCO Style Blue Bars
                fig_daily.add_trace(go.Bar(
                    x=daily_df['date'],
                    y=daily_df['amount'],
                    name='Daily Expense',
                    marker_color='#2563EB',
                    opacity=0.85
                ))
                
                # DESCO Style Yellow Trend Line
                fig_daily.add_trace(go.Scatter(
                    x=daily_df['date'],
                    y=daily_df['amount'],
                    name='Trend',
                    mode='lines+markers',
                    line=dict(color='#F59E0B', width=3),
                    marker=dict(size=7, color='#F59E0B')
                ))

                fig_daily.update_layout(
                    title="Daily Expense Tracker",
                    xaxis_title="Date",
                    yaxis_title="Amount ($)",
                    hovermode="x unified",
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig_daily.update_xaxes(dtick="86400000", tickformat="%d %b")
                st.plotly_chart(fig_daily, use_container_width=True)

            # 2. MONTHLY ANALYTICS TAB
            with tab_monthly:
                monthly_df = df.groupby('month')['amount'].sum().reset_index()

                fig_monthly = go.Figure()
                fig_monthly.add_trace(go.Bar(
                    x=monthly_df['month'],
                    y=monthly_df['amount'],
                    name='Monthly Total',
                    marker_color='#1E40AF'
                ))
                fig_monthly.add_trace(go.Scatter(
                    x=monthly_df['month'],
                    y=monthly_df['amount'],
                    name='Monthly Trend',
                    mode='lines+markers',
                    line=dict(color='#EAB308', width=3),
                    marker=dict(size=8, color='#EAB308')
                ))

                fig_monthly.update_layout(
                    title="12-Month Expense Breakdown",
                    xaxis_title="Month (YYYY-MM)",
                    yaxis_title="Total Amount ($)",
                    hovermode="x unified",
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_monthly, use_container_width=True)

            # 3. CATEGORY BREAKDOWN TAB
            with tab_category:
                cat_df = df.groupby('category')['amount'].sum().reset_index()
                fig_cat = px.pie(cat_df, values='amount', names='category', title='Category Share', hole=0.4)
                st.plotly_chart(fig_cat, use_container_width=True)

            st.divider()

            # --- EXPENSE HISTORY & SEARCH/FILTER SECTION ---
            st.subheader("📊 Expense History & Filtering")

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                selected_cat = st.selectbox("Filter by Category", ["All"] + list(df['category'].unique()))
            with col_f2:
                search_text = st.text_input("Search Description", placeholder="Type to search...")

            filtered_df = df.copy()
            if selected_cat != "All":
                filtered_df = filtered_df[filtered_df['category'] == selected_cat]
            if search_text:
                filtered_df = filtered_df[filtered_df['description'].str.contains(search_text, case=False, na=False)]

            filtered_data = filtered_df.to_dict('records')

            st.write("")
            h1, h2, h3, h4, h5 = st.columns([2, 2, 3, 2, 1])
            h1.markdown("**Date**")
            h2.markdown("**Category**")
            h3.markdown("**Description**")
            h4.markdown("**Amount**")
            h5.markdown("**Action**")
            st.divider()

            for item in filtered_data:
                col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 2, 1])
                col1.write(item["date"])
                col2.write(item["category"])
                col3.write(item.get("description") or "-")
                col4.write(f"${item['amount']:,.2f}")
                
                if col5.button("❌", key=f"del_{item['id']}"):
                    try:
                        supabase.table("expenses").delete().eq("id", item["id"]).execute()
                        st.toast("Expense deleted!", icon="🗑️")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not delete item: {e}")

        else:
            st.info("No expense records found. Add your first expense above!")

    except Exception as e:
        st.error(f"Error loading expenses: {e}")
