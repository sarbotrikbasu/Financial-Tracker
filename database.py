"""
Database Management for Financial Analyzer App
SQLite database for users and investments
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import hashlib

class DatabaseManager:
    """Manage SQLite database for users and investments"""
    
    def __init__(self, db_name: str = "financial_analyzer.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_name, check_same_thread=False)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mobile TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                user_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Investments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investments (
                investment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                instrument_type TEXT NOT NULL,
                instrument_name TEXT NOT NULL,
                scheme_code TEXT,
                symbol TEXT,
                current_investment REAL NOT NULL,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_user(self, name: str, mobile: str, password: str, user_type: str = "client") -> Tuple[bool, str]:
        """Create new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if mobile already exists
            cursor.execute("SELECT mobile FROM users WHERE mobile = ?", (mobile,))
            if cursor.fetchone():
                return False, "Mobile number already registered"
            
            cursor.execute("""
                INSERT INTO users (name, mobile, password, user_type)
                VALUES (?, ?, ?, ?)
            """, (name, mobile, password, user_type))
            
            conn.commit()
            conn.close()
            return True, "User created successfully"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    def authenticate_user(self, mobile: str, password: str, user_type: str) -> Optional[Dict]:
        """Authenticate user and return user details"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, name, mobile, user_type
                FROM users
                WHERE mobile = ? AND password = ? AND user_type = ?
            """, (mobile, password, user_type))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'user_id': user[0],
                    'name': user[1],
                    'mobile': user[2],
                    'user_type': user[3]
                }
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def add_investment(self, user_id: int, instrument_type: str, instrument_name: str,
                      current_investment: float, scheme_code: str = None, 
                      symbol: str = None) -> Tuple[bool, str]:
        """Add investment for a user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO investments (user_id, instrument_type, instrument_name,
                                       scheme_code, symbol, current_investment)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, instrument_type, instrument_name, scheme_code, symbol, current_investment))
            
            conn.commit()
            conn.close()
            return True, "Investment added successfully"
        except Exception as e:
            return False, f"Error adding investment: {str(e)}"
    
    def get_user_investments(self, user_id: int) -> pd.DataFrame:
        """Get all investments for a user"""
        try:
            conn = self.get_connection()
            query = """
                SELECT investment_id, instrument_type, instrument_name,
                       scheme_code, symbol, current_investment, date_added
                FROM investments
                WHERE user_id = ?
                ORDER BY date_added DESC
            """
            df = pd.read_sql_query(query, conn, params=(user_id,))
            conn.close()
            return df
        except Exception as e:
            print(f"Error fetching investments: {e}")
            return pd.DataFrame()
    
    def get_user_by_mobile(self, mobile: str) -> Optional[Dict]:
        """Get user details by mobile number"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, name, mobile, user_type, created_at
                FROM users
                WHERE mobile = ? AND user_type = 'client'
            """, (mobile,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'user_id': user[0],
                    'name': user[1],
                    'mobile': user[2],
                    'user_type': user[3],
                    'created_at': user[4]
                }
            return None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
    
    def delete_investment(self, investment_id: int) -> Tuple[bool, str]:
        """Delete an investment"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM investments WHERE investment_id = ?", (investment_id,))
            
            conn.commit()
            conn.close()
            return True, "Investment deleted successfully"
        except Exception as e:
            return False, f"Error deleting investment: {str(e)}"
    
    def get_all_clients(self) -> pd.DataFrame:
        """Get all client users"""
        try:
            conn = self.get_connection()
            query = """
                SELECT user_id, name, mobile, created_at
                FROM users
                WHERE user_type = 'client'
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error fetching clients: {e}")
            return pd.DataFrame()