"""
Core Financial Analyzer for Mutual Funds and Stocks
"""

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

class FinancialAnalyzer:
    """Analyzer for both mutual funds and stocks"""
    
    MF_BASE_URL = "https://api.mfapi.in/mf"
    
    def __init__(self):
        pass
    
    # ==================== MUTUAL FUND METHODS ====================
    
    def search_mutual_fund(self, fund_name: str) -> List[Dict]:
        """Search for mutual funds by name"""
        try:
            search_url = f"{self.MF_BASE_URL}/search?q={fund_name}"
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error searching mutual funds: {e}")
            return []
    
    def get_mf_details(self, scheme_code: str) -> Optional[Dict]:
        """Get mutual fund details"""
        try:
            url = f"{self.MF_BASE_URL}/{scheme_code}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching fund details: {e}")
            return None
    
    def get_mf_historical_data(self, scheme_code: str) -> pd.DataFrame:
        """Get mutual fund historical NAV data"""
        try:
            fund_data = self.get_mf_details(scheme_code)
            
            if not fund_data or 'data' not in fund_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(fund_data['data'])
            if df.empty:
                return pd.DataFrame()
            
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
            df = df.sort_values('date').reset_index(drop=True)
            df = df.rename(columns={'nav': 'Close'})
            
            return df
        except Exception as e:
            print(f"Error fetching MF historical data: {e}")
            return pd.DataFrame()
    
    # ==================== STOCK METHODS ====================
    
    def search_stock(self, symbol: str) -> Optional[Dict]:
        """Search and validate stock symbol"""
        try:
            if '.' not in symbol:
                test_symbols = [f"{symbol}.NS", f"{symbol}.BO"]
            else:
                test_symbols = [symbol]
            
            for test_symbol in test_symbols:
                try:
                    ticker = yf.Ticker(test_symbol)
                    info = ticker.info
                    
                    if info and 'symbol' in info:
                        return {
                            'symbol': test_symbol,
                            'name': info.get('longName', info.get('shortName', test_symbol)),
                            'sector': info.get('sector', 'N/A'),
                            'industry': info.get('industry', 'N/A'),
                            'exchange': info.get('exchange', 'N/A'),
                            'marketCap': info.get('marketCap', 'N/A')
                        }
                except:
                    continue
            return None
        except Exception as e:
            print(f"Error searching stock: {e}")
            return None
    
    def get_stock_historical_data(self, symbol: str, period: str = "max") -> pd.DataFrame:
        """Get stock historical data"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            
            if df.empty:
                return pd.DataFrame()
            
            df = df.reset_index()
            df.columns = [col.lower() if col == 'Date' else col for col in df.columns]
            
            return df
        except Exception as e:
            print(f"Error fetching stock data: {e}")
            return pd.DataFrame()
    
    # ==================== ANALYSIS METHODS ====================
    
    def calculate_returns(self, df: pd.DataFrame, current_investment: float) -> Dict:
        """Calculate returns and current value"""
        if df.empty or len(df) < 2:
            return {}
        
        latest_price = df.iloc[-1]['Close']
        oldest_price = df.iloc[0]['Close']
        
        # Calculate units based on oldest price
        units = current_investment / oldest_price
        current_value = units * latest_price
        absolute_return = current_value - current_investment
        return_pct = (absolute_return / current_investment) * 100
        
        returns = {
            'current_price': round(latest_price, 2),
            'current_value': round(current_value, 2),
            'invested_amount': round(current_investment, 2),
            'absolute_return': round(absolute_return, 2),
            'return_percentage': round(return_pct, 2),
            'units': round(units, 2),
            'latest_date': df.iloc[-1]['date'].strftime('%Y-%m-%d')
        }
        
        # Calculate period returns
        periods = {
            '1_month': 30,
            '3_months': 90,
            '6_months': 180,
            '1_year': 365,
            '3_years': 1095
        }
        
        for period_name, days in periods.items():
            past_date = df.iloc[-1]['date'] - timedelta(days=days)
            past_data = df[df['date'] <= past_date]
            
            if not past_data.empty:
                past_price = past_data.iloc[-1]['Close']
                period_return = ((latest_price - past_price) / past_price) * 100
                
                # Calculate CAGR for periods >= 1 year
                if days >= 365:
                    years = days / 365
                    cagr = (((latest_price / past_price) ** (1/years)) - 1) * 100
                    returns[f'cagr_{period_name}'] = round(cagr, 2)
                
                returns[f'return_{period_name}'] = round(period_return, 2)
        
        return returns
    
    def calculate_risk_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate risk metrics"""
        if df.empty:
            return {}
        
        df['daily_return'] = df['Close'].pct_change() * 100
        
        stats = {
            'max_price': round(df['Close'].max(), 2),
            'min_price': round(df['Close'].min(), 2),
            'volatility': round(df['daily_return'].std() * (252 ** 0.5), 2),
        }
        
        # Max Drawdown
        cumulative = (1 + df['daily_return']/100).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        stats['max_drawdown'] = round(drawdown.min(), 2)
        
        # Sharpe Ratio
        risk_free_rate = 6.0
        avg_return = df['daily_return'].mean() * 252
        if stats['volatility'] > 0:
            sharpe_ratio = (avg_return - risk_free_rate) / stats['volatility']
            stats['sharpe_ratio'] = round(sharpe_ratio, 2)
        else:
            stats['sharpe_ratio'] = 0
        
        return stats
    
    def analyze_instrument(self, instrument_type: str, instrument_identifier: str, 
                          current_investment: float) -> Dict:
        """Analyze single instrument and return complete metrics"""
        result = {
            'success': False,
            'instrument_type': instrument_type,
            'name': '',
            'returns': {},
            'risk_metrics': {},
            'metadata': {}
        }
        
        try:
            if instrument_type.lower() == 'mutual fund':
                # Get MF data
                fund_details = self.get_mf_details(instrument_identifier)
                if not fund_details:
                    return result
                
                result['name'] = fund_details.get('meta', {}).get('scheme_name', 'Unknown')
                result['metadata'] = fund_details.get('meta', {})
                
                df = self.get_mf_historical_data(instrument_identifier)
                
            else:  # Stock
                stock_info = self.search_stock(instrument_identifier)
                if not stock_info:
                    return result
                
                result['name'] = stock_info['name']
                result['metadata'] = stock_info
                
                df = self.get_stock_historical_data(stock_info['symbol'])
            
            if df.empty:
                return result
            
            # Calculate metrics
            result['returns'] = self.calculate_returns(df, current_investment)
            result['risk_metrics'] = self.calculate_risk_metrics(df)
            result['success'] = True
            
            return result
            
        except Exception as e:
            print(f"Error analyzing instrument: {e}")
            return result
    
    def analyze_portfolio(self, investments_df: pd.DataFrame) -> Dict:
        """Analyze complete portfolio"""
        total_invested = investments_df['current_investment'].sum()
        total_current_value = 0
        
        portfolio_data = []
        
        for _, investment in investments_df.iterrows():
            identifier = investment['scheme_code'] if investment['instrument_type'] == 'Mutual Fund' else investment['symbol']
            
            if pd.isna(identifier):
                continue
            
            analysis = self.analyze_instrument(
                investment['instrument_type'],
                identifier,
                investment['current_investment']
            )
            
            if analysis['success']:
                total_current_value += analysis['returns'].get('current_value', 0)
                portfolio_data.append(analysis)
        
        total_return = total_current_value - total_invested
        return_pct = (total_return / total_invested * 100) if total_invested > 0 else 0
        
        return {
            'total_invested': round(total_invested, 2),
            'total_current_value': round(total_current_value, 2),
            'total_return': round(total_return, 2),
            'return_percentage': round(return_pct, 2),
            'num_investments': len(portfolio_data),
            'instruments': portfolio_data
        }