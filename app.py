import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import calendar
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

    # --- ADD EXPENSE TABS (SINGLE vs MONTHLY FIXED) ---
    st.subheader("➕ Add Expenses")
    add_tab1, add_tab2 = st.tabs(["📌 Add Single Expense", "🗓️ Add Monthly Fixed Expense"])

    # 1. Single Daily Expense Form
    with add_tab1:
        with st.form("single_expense_form", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
            with col1:
                exp_date = st.date_input("Date", value=date.today())
            with col2:
                category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"])
            with col3:
                description = st.text_input("Description", placeholder="e.g. Snacks or Bus Fare")
            with col4:
                amount = st.number_input("Amount ($)", min_value=0.01, step=1.0, key="single_amt")
                
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

    # 2. Monthly Fixed Expense Form
    with add_tab2:
        with st.form("monthly_expense_form", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns([2, 2, 3, 2])
            with col1:
                m_year = st.number_input("Year", min_value=2020, max_value=2030, value=date.today().year)
                m_month = st.selectbox("Month", range(1, 13), index=date.today().month - 1)
            with col2:
                m_category = st.selectbox("Category", ["Bills", "House Rent", "Subscription", "Shopping", "Other"], key="m_cat")
            with col3:
                m_description = st.text_input("Monthly Expense Title", placeholder="e.g. Monthly House Rent")
            with col4:
                m_amount = st.number_input("Amount ($)", min_value=0.01, step=1.0, key="m_amt")
                
            m_submitted = st.form_submit_button("Add Monthly Fixed Expense", use_container_width=True, type="primary")
            
            if m_submitted:
                first_day_of_month = f"{m_year}-{m_month:02d}-01"
                data = {
                    "user_id": user_id,
                    "date": first_day_of_month,
                    "category": m_category,
                    "description": f"[Monthly] {m_description}",
                    "amount": m_amount
                }
                try:
                    supabase.table("expenses").insert(data).execute()
                    st.toast("Monthly expense added successfully!", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add monthly expense: {e}")

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
            st.subheader("📈 Analytics & Monthly Grid")
            tab_daily, tab_grid, tab_monthly, tab_category = st.tabs([
                "📅 Daily Track (Updated)", 
                "🧩 Monthly Tic-Tac Grid", 
                "🗓️ 12-Month Analytics", 
                "🏷️ Category Breakdown"
            ])

            # 1. UPDATED DAILY TRACK TAB
            with tab_daily:
                daily_df = df.groupby('date')['amount'].sum().reset_index()
                daily_df['datetime'] = pd.to_datetime(daily_df['date'])
                daily_df = daily_df.sort_values('datetime')

                if not daily_df.empty:
                    avg_daily = daily_df['amount'].mean()
                    max_daily = daily_df['amount'].max()
                    max_date = daily_df.loc[daily_df['amount'].idxmax()]['date']

                    d_col1, d_col2 = st.columns(2)
                    d_col1.info(f"💡 **Daily Average:** ${avg_daily:,.2f}")
                    d_col2.warning(f"🔥 **Peak Spending Day:** ${max_daily:,.2f} (on {max_date})")

                fig_daily = go.Figure()
                
                # DESCO Style Blue Bar with Data Labels
                fig_daily.add_trace(go.Bar(
                    x=daily_df['date'],
                    y=daily_df['amount'],
                    name='Daily Amount',
                    marker_color='#2563EB',
                    text=[f"${v:,.0f}" for v in daily_df['amount']],
                    textposition='outside',
                    opacity=0.85
                ))
                
                # DESCO Style Yellow Line Overlay
                fig_daily.add_trace(go.Scatter(
                    x=daily_df['date'],
                    y=daily_df['amount'],
                    name='Trend Line',
                    mode='lines+markers',
                    line=dict(color='#F59E0B', width=3),
                    marker=dict(size=8, color='#F59E0B')
                ))

                fig_daily.update_layout(
                    title="Daily Expense Tracking & Trend (DESCO Style)",
                    xaxis_title="Date",
                    yaxis_title="Amount ($)",
                    hovermode="x unified",
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_daily, use_container_width=True)

            # 2. TIC-TAC-TOE STYLE MONTHLY CALENDAR GRID
            with tab_grid:
                st.markdown("##### 🗓️ Month-at-a-Glance Expense Grid")
                
                available_months = sorted(df['month'].unique(), reverse=True)
                selected_month = st.selectbox("Select Month to Inspect:", available_months)

                if selected_month:
                    year, month = map(int, selected_month.split("-"))
                    num_days = calendar.monthrange(year, month)[1]

                    month_df = df[df['month'] == selected_month]
                    daily_sums = month_df.groupby('date')['amount'].sum().to_dict()

                    st.caption(f"Showing daily activity for **{calendar.month_name[month]} {year}**")

                    cols_per_row = 7
                    for day_start in range(1, num_days + 1, cols_per_row):
                        grid_cols = st.columns(cols_per_row)
                        for i in range(cols_per_row):
                            day_num = day_start + i
                            if day_num <= num_days:
                                date_key = f"{year}-{month:02d}-{day_num:02d}"
                                has_expense = date_key in daily_sums
                                day_amount = daily_sums.get(date_key, 0.0)

                                with grid_cols[i]:
                                    if has_expense:
                                        st.success(f"**Day {day_num}**\n\n✅ **${day_amount:,.0f}**")
                                    else:
                                        st.caption(f"Day {day_num}\n\n❌ $0")

            # 3. 12-MONTH ANALYTICS TAB
            with tab_monthly:
                monthly_df = df.groupby('month')['amount'].sum().reset_index()

                fig_monthly = go.Figure()
                fig_monthly.add_trace(go.Bar(
                    x=monthly_df['month'], y=monthly_df['amount'],
                    name='Monthly Total', marker_color='#1E40AF'
                ))
                fig_monthly.add_trace(go.Scatter(
                    x=monthly_df['month'], y=monthly_df['amount'],
                    name='Monthly Trend', mode='lines+markers',
                    line=dict(color='#EAB308', width=3), marker=dict(size=8, color='#EAB308')
                ))

                fig_monthly.update_layout(
                    title="12-Month Expense Breakdown", xaxis_title="Month (YYYY-MM)", yaxis_title="Total Amount ($)",
                    hovermode="x unified", template="plotly_white"
                )
                st.plotly_chart(fig_monthly, use_container_width=True)

            # 4. CATEGORY BREAKDOWN TAB
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
