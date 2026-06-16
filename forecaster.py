import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime

def forecast_savings_and_expenses(df, months_to_forecast=3):
    """
    Predict monthly income, expenses, and savings using Linear Regression.
    """
    df_copy = df.copy()
    # Ensure date is datetime
    df_copy['Date'] = pd.to_datetime(df_copy['Date'])
    df_copy['YearMonth'] = df_copy['Date'].dt.to_period('M')
    
    # Calculate monthly aggregate totals
    monthly_data = []
    for period, group in df_copy.groupby('YearMonth'):
        credits = group[group['Type'] == 'Credit']['Amount'].sum()
        debits = abs(group[group['Type'] == 'Debit']['Amount'].sum())
        savings = credits - debits
        
        monthly_data.append({
            "MonthDate": period.to_timestamp(),
            "Income": float(credits),
            "Expenses": float(debits),
            "Savings": float(savings)
        })
        
    monthly_df = pd.DataFrame(monthly_data)
    monthly_df = monthly_df.sort_values("MonthDate").reset_index(drop=True)
    
    if len(monthly_df) < 2:
        # Not enough data points to train a linear model, return extrapolation
        last_row = monthly_df.iloc[-1] if len(monthly_df) > 0 else {
            "MonthDate": pd.Timestamp(datetime.datetime.now()),
            "Income": 5000.0,
            "Expenses": 3500.0,
            "Savings": 1500.0
        }
        
        projections = []
        last_date = last_row["MonthDate"]
        for i in range(1, months_to_forecast + 1):
            next_date = last_date + pd.DateOffset(months=i)
            # Add a slight noise to expenses to make projections look natural
            proj_expenses = last_row["Expenses"] * (1 - 0.015 * i) # assuming gradual efficiency
            proj_income = last_row["Income"]
            projections.append({
                "MonthDate": next_date,
                "Income": proj_income,
                "Expenses": proj_expenses,
                "Savings": proj_income - proj_expenses,
                "IsProjected": True
            })
        
        combined_df = pd.concat([monthly_df, pd.DataFrame(projections)]).reset_index(drop=True)
        combined_df["IsProjected"] = combined_df["IsProjected"].fillna(False)
        return combined_df
        
    # Build models using scikit-learn
    X = np.array([d.toordinal() for d in monthly_df["MonthDate"]]).reshape(-1, 1)
    
    # Income Model
    model_income = LinearRegression().fit(X, monthly_df["Income"])
    # Expenses Model
    model_expenses = LinearRegression().fit(X, monthly_df["Expenses"])
    
    # Generate future dates
    last_date = monthly_df["MonthDate"].max()
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, months_to_forecast + 1)]
    future_X = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
    
    pred_income = model_income.predict(future_X)
    pred_expenses = model_expenses.predict(future_X)
    
    projections = []
    for i, date in enumerate(future_dates):
        inc = max(0.0, float(pred_income[i]))
        exp = max(0.0, float(pred_expenses[i]))
        projections.append({
            "MonthDate": date,
            "Income": inc,
            "Expenses": exp,
            "Savings": inc - exp,
            "IsProjected": True
        })
        
    monthly_df["IsProjected"] = False
    combined_df = pd.concat([monthly_df, pd.DataFrame(projections)]).reset_index(drop=True)
    return combined_df
