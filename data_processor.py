import pandas as pd
import numpy as np
import io
import datetime

def generate_mock_data():
    # Set seed for reproducible values
    np.random.seed(42)
    
    # Generate 3 months of data (April, May, June 2026)
    transactions = []
    
    for m in [4, 5, 6]:
        # Salary: $5,000/month ($2,500 twice a month)
        transactions.append({
            "Date": f"2026-0{m}-01",
            "Description": "Corporate Salary Direct Deposit",
            "Category": "Income",
            "Amount": 2500.0,
            "Type": "Credit"
        })
        transactions.append({
            "Date": f"2026-0{m}-15",
            "Description": "Corporate Salary Direct Deposit",
            "Category": "Income",
            "Amount": 2500.0,
            "Type": "Credit"
        })
        
        # Monthly Rent: $1,200 on 1st
        transactions.append({
            "Date": f"2026-0{m}-01",
            "Description": "Apt 4B Monthly Rental Pay",
            "Category": "Rent & Housing",
            "Amount": -1200.0,
            "Type": "Debit"
        })
        
        # Utilities
        transactions.append({
            "Date": f"2026-0{m}-05",
            "Description": "Comcast High-Speed Internet",
            "Category": "Utilities & Bills",
            "Amount": -65.0,
            "Type": "Debit"
        })
        transactions.append({
            "Date": f"2026-0{m}-10",
            "Description": "City Power & Light Electric Bill",
            "Category": "Utilities & Bills",
            "Amount": -118.42,
            "Type": "Debit"
        })
        transactions.append({
            "Date": f"2026-0{m}-12",
            "Description": "Municipal District Water Utility",
            "Category": "Utilities & Bills",
            "Amount": -42.50,
            "Type": "Debit"
        })

        # Subscriptions
        transactions.append({
            "Date": f"2026-0{m}-18",
            "Description": "Netflix Inc Premium 4K Plan",
            "Category": "Utilities & Bills",
            "Amount": -22.99,
            "Type": "Debit"
        })
        transactions.append({
            "Date": f"2026-0{m}-22",
            "Description": "Spotify USA Music Subscription",
            "Category": "Utilities & Bills",
            "Amount": -14.99,
            "Type": "Debit"
        })

        # Investments ($500 on the 20th)
        transactions.append({
            "Date": f"2026-0{m}-20",
            "Description": "Vanguard Brokerage ETF VOO",
            "Category": "Investments & Savings",
            "Amount": -500.0,
            "Type": "Debit"
        })
        
        # Groceries (Weekly)
        grocery_days = [3, 11, 18, 25]
        grocery_stores = ["Whole Foods Market", "Trader Joe's", "Safeway Store", "Kroger Grocery"]
        for idx, day in enumerate(grocery_days):
            transactions.append({
                "Date": f"2026-0{m}-{day:02d}",
                "Description": grocery_stores[idx],
                "Category": "Food & Dining",
                "Amount": -float(np.random.randint(95, 175) + 0.35),
                "Type": "Debit"
            })
            
        # Restaurants & Dining Out
        dining_days = [7, 14, 21, 28]
        restaurants = ["Bella Italia Restaurant", "Sushi Zen Grill", "The Gourmet Burger", "Starbucks Coffee Co"]
        for idx, day in enumerate(dining_days):
            transactions.append({
                "Date": f"2026-0{m}-{day:02d}",
                "Description": restaurants[idx],
                "Category": "Food & Dining",
                "Amount": -float(np.random.randint(18, 85) + 0.50),
                "Type": "Debit"
            })
            
        # Shopping & Entertainment
        shopping_days = [8, 16, 24]
        stores = ["Amazon.com Marketplace", "Target Superstore", "Apple Digital Services"]
        for idx, day in enumerate(shopping_days):
            transactions.append({
                "Date": f"2026-0{m}-{day:02d}",
                "Description": stores[idx],
                "Category": "Shopping & Entertainment",
                "Amount": -float(np.random.randint(25, 210) + 0.75),
                "Type": "Debit"
            })

        # Travel & Transport
        travel_days = [4, 13, 27]
        transport_descs = ["Chevron Gas Station", "Uber Trip Support", "Shell Petrol Station"]
        for idx, day in enumerate(travel_days):
            transactions.append({
                "Date": f"2026-0{m}-{day:02d}",
                "Description": transport_descs[idx],
                "Category": "Travel & Transport",
                "Amount": -float(np.random.randint(22, 58) + 0.40),
                "Type": "Debit"
            })

    df = pd.DataFrame(transactions)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=False).reset_index(drop=True)
    return df

def parse_statement(file_bytes, filename):
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            raise ValueError("Unsupported file format. Please upload CSV or Excel.")
        
        # Clean up column names
        df.columns = [c.strip() for c in df.columns]
        
        # Column mapping heuristic (case-insensitive)
        date_col = next((c for c in df.columns if 'date' in c.lower()), None)
        desc_col = next((c for c in df.columns if any(w in c.lower() for w in ['desc', 'detail', 'payee', 'merchant', 'transaction'])), None)
        amount_col = next((c for c in df.columns if 'amount' in c.lower() or 'value' in c.lower() or 'price' in c.lower()), None)
        category_col = next((c for c in df.columns if 'cat' in c.lower() or 'tag' in c.lower()), None)
        
        if not (date_col and desc_col and amount_col):
            raise ValueError("Could not automatically map Date, Description, and Amount columns. Check your CSV schema.")
            
        # Clean and construct standardized DataFrame
        standard_df = pd.DataFrame()
        standard_df['Date'] = pd.to_datetime(df[date_col])
        standard_df['Description'] = df[desc_col].astype(str)
        
        # Handle Amount parsing (strip out currency symbols and commas)
        amounts_series = df[amount_col].astype(str).str.replace('$', '', regex=False).str.replace('€', '', regex=False).str.replace('£', '', regex=False).str.replace(',', '', regex=False)
        standard_df['Amount'] = pd.to_numeric(amounts_series, errors='coerce').fillna(0.0)
        
        if category_col:
            standard_df['Category'] = df[category_col].fillna('Uncategorized').astype(str)
        else:
            # Simple automatic categorization heuristic based on keywords
            categories = []
            for desc in standard_df['Description']:
                desc_lower = desc.lower()
                if any(w in desc_lower for w in ['salary', 'paycheck', 'payroll', 'income', 'direct deposit', 'dividend', 'interest']):
                    categories.append('Income')
                elif any(w in desc_lower for w in ['rent', 'landlord', 'housing', 'mortgage', 'apartment', 'hoa']):
                    categories.append('Rent & Housing')
                elif any(w in desc_lower for w in ['food', 'dining', 'restaurant', 'cafe', 'grocery', 'whole foods', 'trader', 'safeway', 'kroger', 'burger', 'sushi', 'starbucks', 'eats', 'pizza', 'pub', 'deli', 'market']):
                    categories.append('Food & Dining')
                elif any(w in desc_lower for w in ['power', 'light', 'electric', 'water', 'internet', 'comcast', 'netflix', 'spotify', 'subscription', 'utility', 'utilities', 'bill', 'insurance', 'phone', 'verizon', 't-mobile']):
                    categories.append('Utilities & Bills')
                elif any(w in desc_lower for w in ['amazon', 'target', 'apple', 'walmart', 'store', 'retail', 'clothing', 'shopping', 'movie', 'ticket', 'mall', 'best buy', 'steam', 'game']):
                    categories.append('Shopping & Entertainment')
                elif any(w in desc_lower for w in ['vanguard', 'etf', 'stock', 'investment', 'savings', 'fidelity', 'crypto', 'coinbase', 'ira', '401k']):
                    categories.append('Investments & Savings')
                elif any(w in desc_lower for w in ['gas', 'fuel', 'chevron', 'shell', 'uber', 'lyft', 'transit', 'metro', 'travel', 'flight', 'airline', 'cab', 'parking', 'toll']):
                    categories.append('Travel & Transport')
                else:
                    categories.append('Other')
            standard_df['Category'] = categories
            
        # Classify Type (Credit/Debit)
        standard_df['Type'] = np.where(standard_df['Amount'] >= 0, 'Credit', 'Debit')
        
        # Sort and return
        standard_df = standard_df.sort_values('Date', ascending=False).reset_index(drop=True)
        return standard_df
    except Exception as e:
        raise ValueError(f"Error parsing statement: {str(e)}")

def get_monthly_summary(df):
    """
    Computes monthly totals for income, expenses, and savings rate.
    """
    df_copy = df.copy()
    df_copy['YearMonth'] = df_copy['Date'].dt.to_period('M')
    
    summary = []
    for period, group in df_copy.groupby('YearMonth'):
        credits = group[group['Type'] == 'Credit']['Amount'].sum()
        debits = abs(group[group['Type'] == 'Debit']['Amount'].sum())
        savings = credits - debits
        savings_rate = (savings / credits * 100) if credits > 0 else 0
        
        summary.append({
            "Month": str(period),
            "Income": float(credits),
            "Expenses": float(debits),
            "Savings": float(savings),
            "SavingsRate": float(savings_rate)
        })
    
    return pd.DataFrame(summary)
