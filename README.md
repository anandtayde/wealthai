# WealthAI - Streamlit Personal Finance Advisor

WealthAI is a premium, lightweight, interactive dashboard built using **Streamlit** and powered by the **Google Gemini API**. It allows you to parse bank statements, visualize monthly cash flows, track savings rates, forecast future trends with machine learning, and receive personalized coaching from an AI financial advisor.

## Features Showcase
1. **Interactive Dashboard**: Responsive KPI metric boards, Plotly income vs expense charts, category donut charts, and searchable transactions history.
2. **AI Financial Advisor**: In-depth cash flow audit, budget coaching, and interactive chatbot using your actual bank transactions as context.
3. **ML Projections**: Scikit-Learn linear regression models projecting spending and savings.
4. **PDF Report Exporter**: Download customized monthly summary reports formatted with ReportLab.

---

## Installation & Setup

1. **Verify Python is installed** (version 3.9+).
2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure API Keys**:
   Create a `.env` file from `.env.example` and add your Google Gemini API Key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-1.5-flash
   ```
5. **Run the Dashboard**:
   ```bash
   streamlit run app.py
   ```
