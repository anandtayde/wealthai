import streamlit as st
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
import datetime

# Load environment configuration
load_dotenv()

# Import helper modules
from data_processor import generate_mock_data, parse_statement, get_monthly_summary
from advisor import get_financial_analysis, chat_with_advisor
from forecaster import forecast_savings_and_expenses
from pdf_generator import generate_pdf_report

# Configure Streamlit page
st.set_page_config(
    page_title="WealthAI - Personal Finance Advisor",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
def load_custom_css():
    css_path = "assets/styles.css"
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_custom_css()

# Custom HTML metric card
def render_metric_card(label, value, card_type="green"):
    val_class = "metric-value-green"
    if card_type == "blue":
        val_class = "metric-value-blue"
    elif card_type == "red":
        val_class = "metric-value-red"
    
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-lbl">{label}</div>
        <div class="{val_class}">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# Initialize Session States
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = None
if "statement_df" not in st.session_state:
    # Default is empty
    st.session_state.statement_df = None
if "active_data_source" not in st.session_state:
    st.session_state.active_data_source = None

# Sidebar Controls
st.sidebar.markdown('<div class="gradient-header" style="font-size: 1.8rem; margin-bottom: 1rem;">WealthAI</div>', unsafe_allow_html=True)
st.sidebar.caption("Premium Personal Financial Dashboard & AI Advisor")

# API Key config
env_key = os.getenv("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input(
    "Gemini API Key",
    value=env_key,
    type="password",
    help="Get a key from https://aistudio.google.com/ to enable AI features."
)

env_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
selected_model = st.sidebar.selectbox(
    "Gemini Model",
    options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.5-flash"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("Data Input")

uploaded_file = st.sidebar.file_uploader(
    "Upload Bank Statement (CSV / Excel)",
    type=["csv", "xlsx", "xls"],
    help="Upload your bank ledger statements to parse transactions automatically."
)

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.read()
        parsed_df = parse_statement(file_bytes, uploaded_file.name)
        st.session_state.statement_df = parsed_df
        st.session_state.active_data_source = uploaded_file.name
        st.sidebar.success(f"Successfully loaded: {uploaded_file.name}")
    except Exception as e:
        st.sidebar.error(str(e))

if st.sidebar.button("💡 Use Demo Seed Dataset", use_container_width=True):
    mock_df = generate_mock_data()
    st.session_state.statement_df = mock_df
    st.session_state.active_data_source = "Demo Seed Dataset (April - June 2026)"
    # Clear past analysis to recalculate on new data
    st.session_state.ai_analysis = None
    st.sidebar.success("Demo dataset loaded!")

if st.session_state.statement_df is not None:
    if st.sidebar.button("🗑️ Clear Current Data", use_container_width=True):
        st.session_state.statement_df = None
        st.session_state.active_data_source = None
        st.session_state.ai_analysis = None
        st.session_state.chat_history = []
        st.sidebar.info("Data cleared.")
        st.rerun()

st.sidebar.markdown("---")
if st.session_state.active_data_source:
    st.sidebar.caption(f"Active Data: **{st.session_state.active_data_source}**")
else:
    st.sidebar.caption("Active Data: **No data loaded**")

# App Header
st.markdown('<div class="gradient-header">Personal Finance Advisor</div>', unsafe_allow_html=True)
st.markdown("<p style='color: #94A3B8; margin-top: -0.5rem; margin-bottom: 2rem;'>Visualize statement insights, forecast goals, and get expert coaching from your personal financial advisor.</p>", unsafe_allow_html=True)

# Check if data loaded
if st.session_state.statement_df is None:
    st.info("👋 Welcome to **WealthAI**! To get started, upload your bank statement CSV/Excel in the sidebar, or click **Use Demo Seed Dataset** to explore the interactive mock stats.")
    
    # Showcase preview of mockup charts
    st.subheader("Dashboard Preview")
    preview_df = generate_mock_data()
    col1, col2 = st.columns(2)
    with col1:
        sum_df = get_monthly_summary(preview_df)
        fig = px.bar(
            sum_df, x="Month", y=["Income", "Expenses"],
            barmode="group",
            title="Demo Monthly Cash Flows",
            color_discrete_map={"Income": "#10B981", "Expenses": "#EF4444"}
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#F1F5F9")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        cat_df = preview_df[preview_df['Type'] == 'Debit'].groupby('Category')['Amount'].agg(lambda x: abs(x.sum())).reset_index()
        fig = px.pie(
            cat_df, values="Amount", names="Category", hole=0.4,
            title="Demo Expenses by Category",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#F1F5F9")
        st.plotly_chart(fig, use_container_width=True)
        
    st.stop()

# Main Workspace (Tabs)
df = st.session_state.statement_df
tab_dashboard, tab_chat, tab_projections, tab_report = st.tabs([
    "📊 Financial Dashboard", 
    "🤖 AI Financial Advisor", 
    "📈 Forecasts & Projections", 
    "📋 Generate Report"
])

# Summary metrics
total_income = df[df['Type'] == 'Credit']['Amount'].sum()
total_expenses = abs(df[df['Type'] == 'Debit']['Amount'].sum())
net_savings = total_income - total_expenses
savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

with tab_dashboard:
    # Row 1: KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Income / Credits", f"${total_income:,.2f}", "green")
    with col2:
        render_metric_card("Total Expenses / Debits", f"${total_expenses:,.2f}", "red")
    with col3:
        render_metric_card("Net Savings / Cash Flow", f"${net_savings:,.2f}", "blue")
    with col4:
        render_metric_card("Calculated Savings Rate", f"{savings_rate:.1f}%", "green" if savings_rate >= 20 else "blue")
        
    st.markdown("---")
    
    # Row 2: Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Cash Flow Trend Chart
        monthly_summary = get_monthly_summary(df)
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=monthly_summary['Month'], 
            y=monthly_summary['Income'],
            name='Income',
            marker_color='#10B981'
        ))
        fig_trend.add_trace(go.Bar(
            x=monthly_summary['Month'], 
            y=monthly_summary['Expenses'],
            name='Expenses',
            marker_color='#EF4444'
        ))
        fig_trend.update_layout(
            title="Monthly Cash Flows",
            barmode='group',
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#F1F5F9",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with col_chart2:
        # Expense Category Donut Chart
        expenses_df = df[df['Type'] == 'Debit']
        category_df = expenses_df.groupby('Category')['Amount'].agg(lambda x: abs(x.sum())).reset_index()
        category_df = category_df.sort_values(by="Amount", ascending=False)
        
        fig_cat = px.pie(
            category_df, 
            values="Amount", 
            names="Category",
            hole=0.4,
            title="Expenses by Category",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_cat.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#F1F5F9"
        )
        st.plotly_chart(fig_cat, use_container_width=True)
        
    st.markdown("---")
    
    # Row 3: Transaction List
    st.subheader("Transaction History")
    search_query = st.text_input("🔍 Search Description, Category or Amount", "")
    
    filter_df = df.copy()
    if search_query:
        filter_df = filter_df[
            filter_df['Description'].str.contains(search_query, case=False) |
            filter_df['Category'].str.contains(search_query, case=False) |
            filter_df['Amount'].astype(str).str.contains(search_query)
        ]
        
    st.dataframe(
        filter_df.style.format({
            "Date": lambda t: t.strftime("%Y-%m-%d"),
            "Amount": "${:,.2f}"
        }),
        use_container_width=True,
        column_config={
            "Date": st.column_config.DateColumn("Date"),
            "Amount": st.column_config.NumberColumn("Amount"),
            "Type": st.column_config.SelectboxColumn("Type", options=["Credit", "Debit"])
        }
    )

with tab_chat:
    col_ai_left, col_ai_right = st.columns([1, 1])
    
    with col_ai_left:
        st.subheader("🤖 Financial Health Review")
        st.write("Generate a comprehensive analysis of your bank statement, including health scores and strategic recommendations.")
        
        if st.button("📈 Run Financial Statement Analysis", use_container_width=True):
            with st.spinner("WealthAI is reviewing your cash flows..."):
                analysis_result = get_financial_analysis(df, api_key, selected_model)
                st.session_state.ai_analysis = analysis_result
                
        if st.session_state.ai_analysis:
            st.markdown(f'<div class="ai-response-box">', unsafe_allow_html=True)
            st.markdown(st.session_state.ai_analysis)
            st.markdown('</div>', unsafe_allow_html=True)
            
    with col_ai_right:
        st.subheader("💬 Ask Advisor Anything")
        st.write("Ask follow-up questions about your statement, budgeting, or investing goals.")
        
        # Chat history container
        chat_container = st.container(height=450)
        
        # Initial greeting from advisor
        with chat_container:
            st.markdown('<div class="assistant-bubble">Hello! I am WealthAI, your personal finance advisor. I have reviewed your transactions. Ask me questions like:<br><i>- Where am I spending the most?</i><br><i>- How can I increase my savings rate?</i><br><i>- Build a plan to save $10,000.</i></div>', unsafe_allow_html=True)
            for chat in st.session_state.chat_history:
                bubble_class = "user-bubble" if chat["role"] == "user" else "assistant-bubble"
                st.markdown(f'<div class="{bubble_class}">{chat["content"]}</div>', unsafe_allow_html=True)
                
        # Query input
        user_query = st.chat_input("Ask about your budgets, savings, or investments...")
        if user_query:
            # Render user query immediately
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with chat_container:
                st.markdown(f'<div class="user-bubble">{user_query}</div>', unsafe_allow_html=True)
            
            # Request LLM response
            with st.spinner("WealthAI is thinking..."):
                response_text = chat_with_advisor(st.session_state.chat_history, user_query, df, api_key, selected_model)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                with chat_container:
                    st.markdown(f'<div class="assistant-bubble">{response_text}</div>', unsafe_allow_html=True)

with tab_projections:
    st.subheader("📊 Future Cash Flow Forecasting")
    st.write("Using Scikit-Learn linear regression models on your historical monthly cash flows to project the next 3 months.")
    
    forecast_months = st.slider("Select projection range (Months)", 1, 12, 3)
    forecast_df = forecast_savings_and_expenses(df, months_to_forecast=forecast_months)
    
    # Plotly Forecast Chart
    fig_forecast = go.Figure()
    
    # Divide into historical and projected
    hist = forecast_df[forecast_df["IsProjected"] == False]
    proj = forecast_df[forecast_df["IsProjected"] == True]
    
    # Income Historical & Projected
    fig_forecast.add_trace(go.Scatter(
        x=hist["MonthDate"], y=hist["Income"],
        mode='lines+markers', name='Historical Income',
        line=dict(color='#10B981', width=3)
    ))
    fig_forecast.add_trace(go.Scatter(
        x=forecast_df["MonthDate"].iloc[len(hist)-1:], y=forecast_df["Income"].iloc[len(hist)-1:],
        mode='lines', name='Projected Income Trend',
        line=dict(color='#34D399', width=2, dash='dot')
    ))
    
    # Expenses Historical & Projected
    fig_forecast.add_trace(go.Scatter(
        x=hist["MonthDate"], y=hist["Expenses"],
        mode='lines+markers', name='Historical Expenses',
        line=dict(color='#EF4444', width=3)
    ))
    fig_forecast.add_trace(go.Scatter(
        x=forecast_df["MonthDate"].iloc[len(hist)-1:], y=forecast_df["Expenses"].iloc[len(hist)-1:],
        mode='lines', name='Projected Expenses Trend',
        line=dict(color='#F87171', width=2, dash='dot')
    ))
    
    # Savings Historical & Projected
    fig_forecast.add_trace(go.Scatter(
        x=hist["MonthDate"], y=hist["Savings"],
        mode='lines+markers', name='Historical Savings',
        line=dict(color='#3B82F6', width=3)
    ))
    fig_forecast.add_trace(go.Scatter(
        x=forecast_df["MonthDate"].iloc[len(hist)-1:], y=forecast_df["Savings"].iloc[len(hist)-1:],
        mode='lines', name='Projected Savings Trend',
        line=dict(color='#60A5FA', width=2, dash='dot')
    ))
    
    fig_forecast.update_layout(
        title="ML Savings & Cash Flow Projections",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#F1F5F9",
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
    )
    st.plotly_chart(fig_forecast, use_container_width=True)
    
    st.markdown("---")
    
    # Savings Goal Calculator
    st.subheader("🎯 Savings Target Calculator")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        goal_name = st.text_input("What is your savings goal?", "Emergency Fund")
        target_amount = st.number_input("Target Goal Amount ($)", min_value=100.0, value=10000.0, step=500.0)
        current_savings = st.number_input("Current Savings Allocated ($)", min_value=0.0, value=2000.0, step=100.0)
        
    with col_g2:
        monthly_contribute = st.number_input(
            "Estimated Monthly Contribution ($)", 
            min_value=10.0, 
            value=float(max(100.0, net_savings / len(monthly_summary))) if len(monthly_summary) > 0 else 500.0,
            step=50.0,
            help="Defaults to your average monthly savings from the uploaded statements."
        )
        
    remaining_balance = target_amount - current_savings
    if remaining_balance <= 0:
        st.balloons()
        st.success("Congratulations! You have already met your savings target goal! 🎉")
    else:
        months_required = remaining_balance / monthly_contribute
        target_date = datetime.date.today() + pd.DateOffset(months=int(np.ceil(months_required)))
        
        st.markdown(f"""
        <div class="glass-card">
            <h4 style="margin: 0; color: #10B981;">Timeline Estimation</h4>
            <p style="margin: 5px 0 0 0; font-size: 1.1rem;">
                To save the remaining <b>${remaining_balance:,.2f}</b> for your <b>{goal_name}</b>, it will take approximately 
                <b style="color: #3B82F6;">{months_required:.1f} months</b>.
            </p>
            <p style="margin: 5px 0 0 0; font-size: 0.95rem; color: #94A3B8;">
                Estimated Target Completion Date: <b>{target_date.strftime('%B %Y')}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

with tab_report:
    st.subheader("📄 Export Monthly Finance Review PDF")
    st.write("Compile a premium, formatted PDF report outlining your cash flows, category expense percentages, and AI advisory recommendations.")
    
    if st.session_state.ai_analysis is None:
        st.warning("⚠️ Please run the **AI Financial Statement Analysis** in the **AI Financial Advisor** tab first so your recommendations can be compiled in the PDF report.")
    else:
        st.info("AI Insights loaded. You can compile your report now!")
        
        if st.button("🛠️ Compile PDF Report", use_container_width=True):
            with st.spinner("Generating document..."):
                pdf_bytes = generate_pdf_report(df, st.session_state.ai_analysis)
                
                st.download_button(
                    label="📥 Download Financial Report PDF",
                    data=pdf_bytes,
                    file_name="WealthAI_Financial_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("PDF Compiled successfully!")
