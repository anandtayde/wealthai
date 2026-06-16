import google.generativeai as genai
import pandas as pd
import json

def get_gemini_client(api_key):
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai

def generate_financial_context(df):
    """
    Summarize DataFrame metrics to fit nicely inside the LLM prompt.
    """
    total_income = df[df['Type'] == 'Credit']['Amount'].sum()
    total_expenses = abs(df[df['Type'] == 'Debit']['Amount'].sum())
    net_savings = total_income - total_expenses
    
    # Calculate category summary
    category_summary = df[df['Type'] == 'Debit'].groupby('Category')['Amount'].agg(lambda x: abs(x.sum())).reset_index()
    category_summary.columns = ['Category', 'Total Spent']
    category_summary = category_summary.sort_values(by='Total Spent', ascending=False)
    
    # Get top 5 transactions
    top_transactions = df.sort_values(by='Amount', key=abs, ascending=False).head(5)
    top_tx_list = []
    for _, r in top_transactions.iterrows():
        top_tx_list.append(f"{r['Date'].strftime('%Y-%m-%d')} - {r['Description']}: ${r['Amount']}")
        
    context = {
        "total_income": round(float(total_income), 2),
        "total_expenses": round(float(total_expenses), 2),
        "net_savings": round(float(net_savings), 2),
        "savings_rate_pct": round(float((net_savings / total_income * 100) if total_income > 0 else 0), 2),
        "category_expenses": category_summary.to_dict(orient='records'),
        "top_5_largest_transactions": top_tx_list
    }
    
    return context

def get_financial_analysis(df, api_key, model_name="gemini-1.5-flash"):
    if not api_key:
        return "⚠️ **Gemini API Key is missing.** Please set the `GEMINI_API_KEY` in your `.env` file or enter it in the sidebar to get personalized AI advice."
        
    try:
        client = get_gemini_client(api_key)
        context = generate_financial_context(df)
        
        prompt = f"""
You are WealthAI, an elite personal finance advisor. Analyze the following user financial ledger summary and provide a professional, actionable financial health review.

### FINANCIAL LEDGER SUMMARY:
- Total Income: ${context['total_income']:,}
- Total Expenses: ${context['total_expenses']:,}
- Net Savings: ${context['net_savings']:,}
- Savings Rate: {context['savings_rate_pct']}%

### EXPENSES BY CATEGORY:
{json.dumps(context['category_expenses'], indent=2)}

### TOP 5 LARGEST TRANSACTIONS:
{chr(10).join(['- ' + tx for tx in context['top_5_largest_transactions']])}

Please provide:
1. **Overview & Health Score (out of 100)**: A brief evaluation of their current situation.
2. **Key Spending Insights**: Identify any potential areas of overspending or concerning patterns.
3. **Actionable Budget & Saving Suggestions**: 3 specific recommendations to optimize savings.
4. **Investment & Goal Recommendations**: Suggestions on how to allocate net savings based on their profiles.

Keep your response professional, concise, and formatted beautifully in markdown.
"""
        model = client.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ **Error generating AI analysis:** {str(e)}"

def chat_with_advisor(chat_history, user_message, df, api_key, model_name="gemini-1.5-flash"):
    if not api_key:
        return "⚠️ **Gemini API Key is missing.** Please set the `GEMINI_API_KEY` in the sidebar."
        
    try:
        client = get_gemini_client(api_key)
        context = generate_financial_context(df)
        
        # Prepare context injection as system instruction or prepended prompt
        system_instruction = f"""
You are WealthAI, a friendly and experienced personal finance advisor chat assistant. 
You have access to the user's financial profile summary:
- Total Income: ${context['total_income']:,}
- Total Expenses: ${context['total_expenses']:,}
- Net Savings: ${context['net_savings']:,}
- Savings Rate: {context['savings_rate_pct']}%
- Category Expenses: {json.dumps(context['category_expenses'])}
- Largest Transactions: {context['top_5_largest_transactions']}

Use this profile context to answer the user's questions. Be encouraging, precise, and practical.
Keep the advice realistic and explain financial concepts simply if asked.
"""
        # Format the chat history for Gemini API
        contents = []
        # Inject system context
        contents.append({"role": "user", "parts": [f"System Context: {system_instruction}\n\nHi WealthAI! Please help me manage my finances."] })
        contents.append({"role": "model", "parts": ["Hello! I am WealthAI, your personal finance advisor. I have reviewed your transaction metrics. How can I help you optimize your budgets, investments, or savings goals today?"]})
        
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [msg["content"]]})
            
        # Add the current user query
        contents.append({"role": "user", "parts": [user_message]})
        
        model = client.GenerativeModel(model_name)
        response = model.generate_content(contents)
        return response.text
    except Exception as e:
        return f"❌ **Error in AI chat:** {str(e)}"
