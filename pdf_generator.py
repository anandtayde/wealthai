from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import datetime

def generate_pdf_report(df, ai_recommendations):
    """
    Creates a styled PDF monthly review document and returns it as a bytes buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor('#10B981'), # Primary emerald color
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=14,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        textColor=colors.HexColor('#475569'),
        spaceAfter=6,
        leading=13
    )
    
    recommendation_style = ParagraphStyle(
        'AIRecommendationsText',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#0F172A'),
        leading=13
    )
    
    story = []
    
    # Header Title
    story.append(Paragraph("WealthAI — Personal Finance Review", title_style))
    story.append(Paragraph(f"Report Generated: {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}", body_style))
    story.append(Spacer(1, 10))
    
    # 1. Executive Summary Table
    story.append(Paragraph("1. Executive Financial Summary", h2_style))
    
    # Calculate overall stats
    total_income = df[df['Type'] == 'Credit']['Amount'].sum()
    total_expenses = abs(df[df['Type'] == 'Debit']['Amount'].sum())
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
    
    summary_data = [
        ["Financial KPI Metric", "Value Summary"],
        ["Total Credits / Income", f"${total_income:,.2f}"],
        ["Total Debits / Expenses", f"${total_expenses:,.2f}"],
        ["Net Cash Position / Savings", f"${net_savings:,.2f}"],
        ["Calculated Savings Rate", f"{savings_rate:.1f}%"]
    ]
    
    t_summary = Table(summary_data, colWidths=[240, 160])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#10B981')),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F8FAFC'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    
    story.append(t_summary)
    story.append(Spacer(1, 10))
    
    # 2. Category Breakdown
    story.append(Paragraph("2. Expense Breakdown by Category", h2_style))
    
    category_summary = df[df['Type'] == 'Debit'].groupby('Category')['Amount'].agg(lambda x: abs(x.sum())).reset_index()
    category_summary.columns = ['Category', 'Amount']
    category_summary = category_summary.sort_values(by='Amount', ascending=False)
    
    cat_data = [["Expense Category", "Total Amount Spent", "Percentage of Debits"]]
    for _, row in category_summary.iterrows():
        pct = (row['Amount'] / total_expenses * 100) if total_expenses > 0 else 0
        cat_data.append([
            row['Category'],
            f"${row['Amount']:,.2f}",
            f"{pct:.1f}%"
        ])
        
    t_cat = Table(cat_data, colWidths=[200, 110, 110])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (2,0), colors.HexColor('#334155')),
        ('TEXTCOLOR', (0,0), (2,0), colors.white),
        ('FONTNAME', (0,0), (2,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F8FAFC'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('ALIGN', (1,0), (2,-1), 'RIGHT'),
    ]))
    story.append(t_cat)
    story.append(Spacer(1, 15))
    
    # PageBreak to separate data and AI insights
    story.append(PageBreak())
    
    # 3. AI Insights
    story.append(Paragraph("3. AI Financial Advisor Strategic Review", h2_style))
    
    # Simple markdown-to-pdf paragraphs parsing
    paragraphs = ai_recommendations.split('\n')
    
    ai_story = []
    for p in paragraphs:
        p_text = p.strip()
        if p_text:
            # Format bold tags
            formatted_p = p_text
            # Simple bold parser replacing **text** with <b>text</b>
            import re
            formatted_p = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted_p)
            
            # Check if it looks like a list item or heading
            if p_text.startswith('#'):
                p_text_clean = p_text.lstrip('#').strip()
                ai_story.append(Paragraph(f"<b>{p_text_clean}</b>", h2_style))
                ai_story.append(Spacer(1, 3))
            elif p_text.startswith('-') or p_text.startswith('*'):
                p_text_clean = re.sub(r'^[-*]\s*', '', formatted_p)
                ai_story.append(Paragraph(f"• {p_text_clean}", recommendation_style))
                ai_story.append(Spacer(1, 4))
            else:
                ai_story.append(Paragraph(formatted_p, recommendation_style))
                ai_story.append(Spacer(1, 5))
                
    # Wrap AI recommendations in a background table card
    ai_table = Table([[ai_story]], colWidths=[520])
    ai_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FDF4')), # Light green background
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#A7F3D0')),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    
    story.append(ai_table)
    
    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
