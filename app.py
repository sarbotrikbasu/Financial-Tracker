"""
Financial Analyzer Portfolio Management System
Streamlit Application
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import DatabaseManager
from financial_analyzer import FinancialAnalyzer
from portfolio import PortfolioManager
import time

# Page configuration
st.set_page_config(
    page_title="UnoCap Portfolio Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize managers
@st.cache_resource
def get_managers():
    return DatabaseManager(), FinancialAnalyzer(), PortfolioManager()

db, analyzer, portfolio_mgr = get_managers()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-msg {
        color: #28a745;
        font-weight: bold;
    }
    .error-msg {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

def logout():
    """Logout function"""
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.page = 'login'
    st.rerun()

# ==================== LOGIN PAGE ====================
def login_page():
    """Login and signup page"""
    st.markdown('<div class="main-header">📊 UnoCap Portfolio Manager</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Client Login", "Client Signup", "Admin Login"])
    
    # Client Login
    with tab1:
        st.subheader("Client Login")
        with st.form("client_login_form"):
            mobile = st.text_input("Mobile Number", max_chars=10)
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if password != "UnoCap":
                    st.error("❌ Invalid password")
                else:
                    user = db.authenticate_user(mobile, password, 'client')
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user
                        st.success(f"✅ Welcome {user['name']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ User not found. Please sign up first.")
    
    # Client Signup
    with tab2:
        st.subheader("Client Signup")
        with st.form("client_signup_form"):
            name = st.text_input("Full Name")
            mobile = st.text_input("Mobile Number", max_chars=10)
            password = st.text_input("Password", type="password", value="UnoCap", disabled=True)
            submit = st.form_submit_button("Sign Up")
            
            if submit:
                if not name or not mobile:
                    st.error("❌ Please fill all fields")
                elif len(mobile) != 10 or not mobile.isdigit():
                    st.error("❌ Please enter a valid 10-digit mobile number")
                else:
                    success, message = db.create_user(name, mobile, "UnoCap", "client")
                    if success:
                        st.success(f"✅ {message}. Please login.")
                    else:
                        st.error(f"❌ {message}")
    
    # Admin Login
    with tab3:
        st.subheader("Admin Login")
        with st.form("admin_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username == "Sarbo" and password == "Sarbo":
                    st.session_state.logged_in = True
                    st.session_state.user_data = {
                        'user_id': 0,
                        'name': 'Admin',
                        'mobile': 'admin',
                        'user_type': 'admin'
                    }
                    st.success("✅ Admin login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid admin credentials")

# ==================== CLIENT DASHBOARD ====================
def client_dashboard():
    """Client dashboard with portfolio management"""
    
    st.sidebar.title(f"👤 {st.session_state.user_data['name']}")
    st.sidebar.info(f"Mobile: {st.session_state.user_data['mobile']}")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
    
    st.title("📊 My Portfolio")
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📈 Add Investment", "💼 My Investments", "📊 Portfolio Analytics"])
    
    # Tab 1: Add Investment
    with tab1:
        st.subheader("Add New Investment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            instrument_type = st.selectbox("Instrument Type", ["Stock", "Mutual Fund"])
        
        with col2:
            current_investment = st.number_input("Current Investment (₹)", min_value=100.0, step=100.0)
        
        if instrument_type == "Mutual Fund":
            st.info("💡 Search for mutual funds by name")
            search_term = st.text_input("Search Mutual Fund", placeholder="e.g., HDFC Top 100, SBI Bluechip")
            
            if search_term:
                with st.spinner("Searching..."):
                    results = analyzer.search_mutual_fund(search_term)
                
                if results:
                    fund_options = {f"{fund['schemeName']}": fund['schemeCode'] 
                                  for fund in results[:20]}
                    
                    selected_fund = st.selectbox("Select Fund", list(fund_options.keys()))
                    
                    if st.button("Add Mutual Fund", type="primary"):
                        scheme_code = fund_options[selected_fund]
                        success, message = db.add_investment(
                            st.session_state.user_data['user_id'],
                            "Mutual Fund",
                            selected_fund,
                            current_investment,
                            scheme_code=scheme_code
                        )
                        if success:
                            st.success(f"✅ {message}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.warning("No mutual funds found. Try different keywords.")
        
        else:  # Stock
            st.info("💡 Enter stock symbol (e.g., RELIANCE.NS, TCS, INFY.BO)")
            stock_symbol = st.text_input("Stock Symbol", placeholder="e.g., RELIANCE.NS").upper()
            
            if stock_symbol:
                with st.spinner("Validating stock..."):
                    stock_info = analyzer.search_stock(stock_symbol)
                
                if stock_info:
                    st.success(f"✅ Found: {stock_info['name']} ({stock_info['symbol']})")
                    st.caption(f"Sector: {stock_info.get('sector', 'N/A')} | Exchange: {stock_info.get('exchange', 'N/A')}")
                    
                    if st.button("Add Stock", type="primary"):
                        success, message = db.add_investment(
                            st.session_state.user_data['user_id'],
                            "Stock",
                            stock_info['name'],
                            current_investment,
                            symbol=stock_info['symbol']
                        )
                        if success:
                            st.success(f"✅ {message}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("❌ Stock not found. Please check the symbol.")
    
    # Tab 2: My Investments
    with tab2:
        st.subheader("My Investments")
        
        investments_df = db.get_user_investments(st.session_state.user_data['user_id'])
        
        if investments_df.empty:
            st.info("📝 No investments added yet. Add your first investment!")
        else:
            st.dataframe(investments_df[['instrument_type', 'instrument_name', 'current_investment', 'date_added']], 
                        use_container_width=True)
            
            # Option to delete investment
            with st.expander("🗑️ Delete Investment"):
                investment_to_delete = st.selectbox(
                    "Select investment to delete",
                    options=investments_df['investment_id'].tolist(),
                    format_func=lambda x: investments_df[investments_df['investment_id']==x]['instrument_name'].values[0]
                )
                
                if st.button("Delete", type="secondary"):
                    success, message = db.delete_investment(investment_to_delete)
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    # Tab 3: Portfolio Analytics
    with tab3:
        st.subheader("Portfolio Analytics")
        
        investments_df = db.get_user_investments(st.session_state.user_data['user_id'])
        
        if investments_df.empty:
            st.info("📝 No investments to analyze. Add investments first!")
        else:
            with st.spinner("Analyzing portfolio... This may take a moment."):
                portfolio_analysis = analyzer.analyze_portfolio(investments_df)
            
            # Portfolio Summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Invested", f"₹{portfolio_analysis['total_invested']:,.0f}")
            
            with col2:
                st.metric("Current Value (Est.)", f"₹{portfolio_analysis['total_current_value']:,.0f}")
            
            with col3:
                return_val = portfolio_analysis['total_return']
                st.metric("Total Returns (Est.)", f"₹{return_val:,.0f}", 
                         delta=f"{portfolio_analysis['return_percentage']:.2f}%")
            
            with col4:
                st.metric("Investments", portfolio_analysis['num_investments'])
            
            st.info("ℹ️ **Note:** Portfolio returns are estimated based on historical performance from available data. Actual returns depend on your purchase date and price.")
            
            st.divider()
            
            # Individual Investment Details
            if portfolio_analysis['instruments']:
                st.subheader("Investment Holdings")
                
                # Create a simple summary table
                holdings_data = []
                for instrument in portfolio_analysis['instruments']:
                    holdings_data.append({
                        'Instrument': instrument['name'],
                        'Type': instrument['instrument_type'],
                        'Invested Amount (₹)': f"₹{investments_df[investments_df['instrument_name']==instrument['name']]['current_investment'].values[0]:,.2f}" if len(investments_df[investments_df['instrument_name']==instrument['name']]) > 0 else 'N/A'
                    })
                
                holdings_df = pd.DataFrame(holdings_data)
                st.dataframe(holdings_df, use_container_width=True, hide_index=True)
                
                st.divider()
                
                # Detailed analysis for each investment
                st.subheader("📊 Detailed Fund Analysis & Metrics")
                
                for idx, instrument in enumerate(portfolio_analysis['instruments'], 1):
                    with st.expander(f"**{idx}. {instrument['name']}** - {instrument['instrument_type']}", expanded=(idx==1)):
                        
                        # Basic Info Section
                        st.markdown("#### 📋 Instrument Information")
                        metadata = instrument.get('metadata', {})
                        
                        if instrument['instrument_type'] == 'Mutual Fund':
                            info_cols = st.columns(3)
                            with info_cols[0]:
                                st.metric("Scheme Code", metadata.get('scheme_code', 'N/A'))
                            with info_cols[1]:
                                st.metric("Fund House", metadata.get('fund_house', 'N/A'))
                            with info_cols[2]:
                                st.metric("Category", metadata.get('scheme_category', 'N/A'))
                            
                            st.caption(f"**Scheme Type:** {metadata.get('scheme_type', 'N/A')}")
                        else:  # Stock
                            info_cols = st.columns(4)
                            with info_cols[0]:
                                st.metric("Symbol", metadata.get('symbol', 'N/A'))
                            with info_cols[1]:
                                st.metric("Exchange", metadata.get('exchange', 'N/A'))
                            with info_cols[2]:
                                st.metric("Sector", metadata.get('sector', 'N/A'))
                            with info_cols[3]:
                                mkt_cap = metadata.get('marketCap', 'N/A')
                                if isinstance(mkt_cap, (int, float)):
                                    st.metric("Market Cap", f"₹{mkt_cap/10000000:,.0f} Cr")
                                else:
                                    st.metric("Market Cap", "N/A")
                        
                        st.divider()
                        
                        # Current Price & Investment
                        st.markdown("#### 💰 Your Investment")
                        returns = instrument.get('returns', {})
                        
                        inv_cols = st.columns(4)
                        with inv_cols[0]:
                            invested = investments_df[investments_df['instrument_name']==instrument['name']]['current_investment'].values[0] if len(investments_df[investments_df['instrument_name']==instrument['name']]) > 0 else 0
                            st.metric("Your Investment", f"₹{invested:,.2f}")
                        with inv_cols[1]:
                            st.metric("Current NAV/Price", f"₹{returns.get('current_price', 0):.2f}")
                        with inv_cols[2]:
                            st.metric("Latest Date", returns.get('latest_date', 'N/A'))
                        with inv_cols[3]:
                            st.metric("Units (Estimated)", f"{returns.get('units', 0):.2f}")
                        
                        st.divider()
                        
                        # Performance Metrics
                        st.markdown("#### 📈 Performance Returns")
                        st.caption("*Returns are calculated based on historical performance of the instrument*")
                        
                        # Period Returns Table
                        period_data = []
                        period_labels = {
                            'return_1_month': '1 Month',
                            'return_3_months': '3 Months',
                            'return_6_months': '6 Months',
                            'return_1_year': '1 Year',
                            'return_3_years': '3 Years'
                        }
                        
                        for key, label in period_labels.items():
                            if key in returns:
                                row_data = {
                                    'Period': label,
                                    'Return (%)': f"{returns[key]:.2f}%"
                                }
                                # Add CAGR if available
                                cagr_key = key.replace('return_', 'cagr_')
                                if cagr_key in returns:
                                    row_data['CAGR (%)'] = f"{returns[cagr_key]:.2f}%"
                                period_data.append(row_data)
                        
                        if period_data:
                            period_df = pd.DataFrame(period_data)
                            st.dataframe(period_df, use_container_width=True, hide_index=True)
                        else:
                            st.info("Period returns data not available")
                        
                        st.divider()
                        
                        # Risk Metrics
                        st.markdown("#### ⚠️ Risk Metrics")
                        risk = instrument.get('risk_metrics', {})
                        
                        risk_cols = st.columns(4)
                        with risk_cols[0]:
                            st.metric("Volatility (Annual)", f"{risk.get('volatility', 0):.2f}%")
                        with risk_cols[1]:
                            st.metric("Sharpe Ratio", f"{risk.get('sharpe_ratio', 0):.2f}")
                        with risk_cols[2]:
                            st.metric("Max Drawdown", f"{risk.get('max_drawdown', 0):.2f}%")
                        with risk_cols[3]:
                            st.metric("52-Week High", f"₹{risk.get('max_price', 0):.2f}")
                        
                        st.caption(f"**52-Week Low:** ₹{risk.get('min_price', 0):.2f}")
                        
                        # Risk interpretation
                        volatility = risk.get('volatility', 0)
                        if volatility < 10:
                            risk_level = "🟢 Low Risk"
                        elif volatility < 20:
                            risk_level = "🟡 Moderate Risk"
                        else:
                            risk_level = "🔴 High Risk"
                        
                        st.info(f"**Risk Level:** {risk_level} | **Interpretation:** " + 
                               ("Lower volatility indicates more stable returns" if volatility < 15 else "Higher volatility indicates more fluctuation in returns"))
                        
                        st.markdown("---")
            
            # Download Report
            st.subheader("📄 Download Report")
            
            if st.button("Generate Report", type="primary"):
                user_details = {
                    'name': st.session_state.user_data['name'],
                    'mobile': st.session_state.user_data['mobile'],
                    'created_at': 'N/A'
                }
                
                report_text = portfolio_mgr.generate_client_report(user_details, portfolio_analysis)
                
                st.download_button(
                    label="📥 Download Portfolio Report",
                    data=report_text,
                    file_name=f"portfolio_report_{st.session_state.user_data['mobile']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

# ==================== ADMIN DASHBOARD ====================
def admin_dashboard():
    """Admin dashboard to view all clients"""
    
    st.sidebar.title("👨‍💼 Admin Panel")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()
    
    st.title("🔐 Admin Dashboard")
    
    tab1, tab2 = st.tabs(["👥 All Clients", "🔍 Search Client"])
    
    # Tab 1: All Clients
    with tab1:
        st.subheader("All Registered Clients")
        
        clients_df = db.get_all_clients()
        
        if clients_df.empty:
            st.info("No clients registered yet.")
        else:
            st.dataframe(clients_df, use_container_width=True)
            st.caption(f"Total Clients: {len(clients_df)}")
    
    # Tab 2: Search Client
    with tab2:
        st.subheader("Search Client by Mobile Number")
        
        mobile_search = st.text_input("Enter Mobile Number", max_chars=10)
        
        if st.button("Search", type="primary") and mobile_search:
            user = db.get_user_by_mobile(mobile_search)
            
            if not user:
                st.error("❌ Client not found")
            else:
                st.success(f"✅ Client Found: {user['name']}")
                
                # Display user details
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Name:** {user['name']}")
                    st.info(f"**Mobile:** {user['mobile']}")
                
                with col2:
                    st.info(f"**User Type:** {user['user_type']}")
                    st.info(f"**Registered:** {user['created_at']}")
                
                st.divider()
                
                # Get investments
                investments_df = db.get_user_investments(user['user_id'])
                
                if investments_df.empty:
                    st.warning("This client has no investments yet.")
                else:
                    st.subheader("📊 Portfolio Details")
                    
                    with st.spinner("Analyzing portfolio..."):
                        portfolio_analysis = analyzer.analyze_portfolio(investments_df)
                    
                    # Portfolio Summary
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Invested", f"₹{portfolio_analysis['total_invested']:,.0f}")
                    
                    with col2:
                        st.metric("Current Value (Est.)", f"₹{portfolio_analysis['total_current_value']:,.0f}")
                    
                    with col3:
                        st.metric("Total Returns (Est.)", f"₹{portfolio_analysis['total_return']:,.0f}")
                    
                    with col4:
                        st.metric("Return % (Est.)", f"{portfolio_analysis['return_percentage']:.2f}%")
                    
                    st.info("ℹ️ **Note:** Returns are estimated based on historical performance. Actual returns depend on purchase date and price.")
                    
                    st.divider()
                    
                    # Investment List
                    st.subheader("📊 Portfolio Holdings")
                    
                    # Simple holdings table
                    holdings_data = []
                    for instrument in portfolio_analysis['instruments']:
                        holdings_data.append({
                            'Instrument': instrument['name'],
                            'Type': instrument['instrument_type'],
                            'Invested Amount (₹)': f"₹{investments_df[investments_df['instrument_name']==instrument['name']]['current_investment'].values[0]:,.2f}" if len(investments_df[investments_df['instrument_name']==instrument['name']]) > 0 else 'N/A'
                        })
                    
                    holdings_df = pd.DataFrame(holdings_data)
                    st.dataframe(holdings_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    
                    # Detailed Fund Analysis
                    st.subheader("📈 Detailed Fund Analysis & Metrics")
                    
                    for idx, instrument in enumerate(portfolio_analysis['instruments'], 1):
                        with st.expander(f"**{idx}. {instrument['name']}** - {instrument['instrument_type']}", expanded=False):
                            
                            # Basic Info Section
                            st.markdown("#### 📋 Instrument Information")
                            metadata = instrument.get('metadata', {})
                            
                            if instrument['instrument_type'] == 'Mutual Fund':
                                info_cols = st.columns(3)
                                with info_cols[0]:
                                    st.metric("Scheme Code", metadata.get('scheme_code', 'N/A'))
                                with info_cols[1]:
                                    st.metric("Fund House", metadata.get('fund_house', 'N/A'))
                                with info_cols[2]:
                                    st.metric("Category", metadata.get('scheme_category', 'N/A'))
                                
                                st.caption(f"**Scheme Type:** {metadata.get('scheme_type', 'N/A')}")
                            else:  # Stock
                                info_cols = st.columns(4)
                                with info_cols[0]:
                                    st.metric("Symbol", metadata.get('symbol', 'N/A'))
                                with info_cols[1]:
                                    st.metric("Exchange", metadata.get('exchange', 'N/A'))
                                with info_cols[2]:
                                    st.metric("Sector", metadata.get('sector', 'N/A'))
                                with info_cols[3]:
                                    mkt_cap = metadata.get('marketCap', 'N/A')
                                    if isinstance(mkt_cap, (int, float)):
                                        st.metric("Market Cap", f"₹{mkt_cap/10000000:,.0f} Cr")
                                    else:
                                        st.metric("Market Cap", "N/A")
                            
                            st.divider()
                            
                            # Current Price & Investment
                            st.markdown("#### 💰 Client Investment")
                            returns = instrument.get('returns', {})
                            
                            inv_cols = st.columns(4)
                            with inv_cols[0]:
                                invested = investments_df[investments_df['instrument_name']==instrument['name']]['current_investment'].values[0] if len(investments_df[investments_df['instrument_name']==instrument['name']]) > 0 else 0
                                st.metric("Client Investment", f"₹{invested:,.2f}")
                            with inv_cols[1]:
                                st.metric("Current NAV/Price", f"₹{returns.get('current_price', 0):.2f}")
                            with inv_cols[2]:
                                st.metric("Latest Date", returns.get('latest_date', 'N/A'))
                            with inv_cols[3]:
                                st.metric("Units (Estimated)", f"{returns.get('units', 0):.2f}")
                            
                            st.divider()
                            
                            # Performance Metrics
                            st.markdown("#### 📈 Performance Returns")
                            st.caption("*Returns are calculated based on historical performance of the instrument*")
                            
                            # Period Returns Table
                            period_data = []
                            period_labels = {
                                'return_1_month': '1 Month',
                                'return_3_months': '3 Months',
                                'return_6_months': '6 Months',
                                'return_1_year': '1 Year',
                                'return_3_years': '3 Years'
                            }
                            
                            for key, label in period_labels.items():
                                if key in returns:
                                    row_data = {
                                        'Period': label,
                                        'Return (%)': f"{returns[key]:.2f}%"
                                    }
                                    # Add CAGR if available
                                    cagr_key = key.replace('return_', 'cagr_')
                                    if cagr_key in returns:
                                        row_data['CAGR (%)'] = f"{returns[cagr_key]:.2f}%"
                                    period_data.append(row_data)
                            
                            if period_data:
                                period_df = pd.DataFrame(period_data)
                                st.dataframe(period_df, use_container_width=True, hide_index=True)
                            else:
                                st.info("Period returns data not available")
                            
                            st.divider()
                            
                            # Risk Metrics
                            st.markdown("#### ⚠️ Risk Metrics")
                            risk = instrument.get('risk_metrics', {})
                            
                            risk_cols = st.columns(4)
                            with risk_cols[0]:
                                st.metric("Volatility (Annual)", f"{risk.get('volatility', 0):.2f}%")
                            with risk_cols[1]:
                                st.metric("Sharpe Ratio", f"{risk.get('sharpe_ratio', 0):.2f}")
                            with risk_cols[2]:
                                st.metric("Max Drawdown", f"{risk.get('max_drawdown', 0):.2f}%")
                            with risk_cols[3]:
                                st.metric("52-Week High", f"₹{risk.get('max_price', 0):.2f}")
                            
                            st.caption(f"**52-Week Low:** ₹{risk.get('min_price', 0):.2f}")
                            
                            # Risk interpretation
                            volatility = risk.get('volatility', 0)
                            if volatility < 10:
                                risk_level = "🟢 Low Risk"
                            elif volatility < 20:
                                risk_level = "🟡 Moderate Risk"
                            else:
                                risk_level = "🔴 High Risk"
                            
                            st.info(f"**Risk Level:** {risk_level} | **Interpretation:** " + 
                                   ("Lower volatility indicates more stable returns" if volatility < 15 else "Higher volatility indicates more fluctuation in returns"))
                            
                            st.markdown("---")
                    
                    # Download Report
                    st.subheader("📄 Download Client Report")
                    
                    report_text = portfolio_mgr.generate_client_report(user, portfolio_analysis)
                    
                    st.download_button(
                        label="📥 Download Full Report",
                        data=report_text,
                        file_name=f"client_report_{user['mobile']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )

# ==================== MAIN APP LOGIC ====================
def main():
    """Main application logic"""
    
    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.user_data['user_type'] == 'admin':
            admin_dashboard()
        else:
            client_dashboard()

if __name__ == "__main__":
    main()