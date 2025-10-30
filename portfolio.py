"""
Portfolio Management and Report Generation
"""

from datetime import datetime
from typing import Dict
import pandas as pd

class PortfolioManager:
    """Manage portfolio and generate reports"""
    
    def generate_client_report(self, user_details: Dict, portfolio_analysis: Dict) -> str:
        """Generate comprehensive client portfolio report"""
        
        report = f"""
{'='*80}
                    PORTFOLIO ANALYSIS REPORT
{'='*80}

CLIENT INFORMATION
{'-'*80}
Name              : {user_details.get('name', 'N/A')}
Mobile            : {user_details.get('mobile', 'N/A')}
Client Since      : {user_details.get('created_at', 'N/A')}

PORTFOLIO SUMMARY
{'-'*80}
Total Investments     : {portfolio_analysis['num_investments']}
Total Invested Amount : ₹{portfolio_analysis['total_invested']:,.2f}
Current Portfolio Value: ₹{portfolio_analysis['total_current_value']:,.2f}
Total Returns         : ₹{portfolio_analysis['total_return']:,.2f}
Return Percentage     : {portfolio_analysis['return_percentage']:.2f}%

{'='*80}
INDIVIDUAL INVESTMENTS
{'='*80}
"""
        
        for idx, instrument in enumerate(portfolio_analysis['instruments'], 1):
            returns = instrument.get('returns', {})
            risk = instrument.get('risk_metrics', {})
            metadata = instrument.get('metadata', {})
            
            report += f"""
{'='*80}
INVESTMENT #{idx}: {instrument['name']}
{'='*80}

INSTRUMENT INFORMATION
{'-'*80}
Type                  : {instrument['instrument_type']}
"""
            
            # Add metadata based on instrument type
            if instrument['instrument_type'] == 'Mutual Fund':
                report += f"""Scheme Code           : {metadata.get('scheme_code', 'N/A')}
Fund House            : {metadata.get('fund_house', 'N/A')}
Scheme Category       : {metadata.get('scheme_category', 'N/A')}
Scheme Type           : {metadata.get('scheme_type', 'N/A')}"""
            else:  # Stock
                mkt_cap = metadata.get('marketCap', 'N/A')
                mkt_cap_str = f"₹{mkt_cap/10000000:,.0f} Cr" if isinstance(mkt_cap, (int, float)) else str(mkt_cap)
                report += f"""Symbol                : {metadata.get('symbol', 'N/A')}
Exchange              : {metadata.get('exchange', 'N/A')}
Sector                : {metadata.get('sector', 'N/A')}
Industry              : {metadata.get('industry', 'N/A')}
Market Cap            : {mkt_cap_str}"""
            
            report += f"""

CURRENT HOLDINGS
{'-'*80}
Current NAV/Price     : ₹{returns.get('current_price', 0):,.2f}
Latest Date           : {returns.get('latest_date', 'N/A')}
Units Held (Est.)     : {returns.get('units', 0):.2f}
Invested Amount       : ₹{returns.get('invested_amount', 0):,.2f}
Current Value (Est.)  : ₹{returns.get('current_value', 0):,.2f}

PERFORMANCE RETURNS
{'-'*80}
Note: Returns are based on historical instrument performance
"""
            
            # Add period returns if available
            period_returns = {
                'return_1_month': '1 Month',
                'return_3_months': '3 Months',
                'return_6_months': '6 Months',
                'return_1_year': '1 Year',
                'return_3_years': '3 Years'
            }
            
            for key, label in period_returns.items():
                if key in returns:
                    report += f"{label:<20}: {returns[key]:>8.2f}%"
                    cagr_key = key.replace('return_', 'cagr_')
                    if cagr_key in returns:
                        report += f"  (CAGR: {returns[cagr_key]:.2f}%)"
                    report += "\n"
            
            report += f"""
RISK METRICS
{'-'*80}
Annualized Volatility : {risk.get('volatility', 'N/A')}%
Sharpe Ratio          : {risk.get('sharpe_ratio', 'N/A')}
Max Drawdown          : {risk.get('max_drawdown', 'N/A')}%
52-Week High          : ₹{risk.get('max_price', 'N/A')}
52-Week Low           : ₹{risk.get('min_price', 'N/A')}

RISK ASSESSMENT
{'-'*80}"""
            
            volatility = risk.get('volatility', 0)
            if volatility < 10:
                risk_level = "Low Risk"
                risk_desc = "This instrument shows low volatility, indicating relatively stable returns."
            elif volatility < 20:
                risk_level = "Moderate Risk"
                risk_desc = "This instrument shows moderate volatility with balanced risk-return profile."
            else:
                risk_level = "High Risk"
                risk_desc = "This instrument shows high volatility, indicating significant fluctuations in returns."
            
            report += f"""
Risk Level            : {risk_level}
Interpretation        : {risk_desc}
"""
        
        report += f"""

{'='*80}
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}
"""
        
        return report
    
    def generate_investment_summary_df(self, portfolio_analysis: Dict) -> pd.DataFrame:
        """Generate DataFrame summary of all investments"""
        
        summary_data = []
        
        for instrument in portfolio_analysis['instruments']:
            returns = instrument.get('returns', {})
            
            summary_data.append({
                'Instrument': instrument['name'],
                'Type': instrument['instrument_type'],
                'Invested (₹)': returns.get('invested_amount', 0),
                'Current Value (₹)': returns.get('current_value', 0),
                'Returns (₹)': returns.get('absolute_return', 0),
                'Returns (%)': returns.get('return_percentage', 0),
                'Current Price': returns.get('current_price', 0)
            })
        
        return pd.DataFrame(summary_data)