import json,csv,os
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.colors import HexColor,white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
P=Path('/mnt/data/Track_A_Olist_Sales');R=P/'results';Q=json.loads((R/'validation_summary.json').read_text());
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';pdfmetrics.registerFont(TTFont('DejaVu',font));pdfmetrics.registerFont(TTFont('DejaVuB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
NAVY=HexColor('#142A3A');TEAL=HexColor('#0B8174');PALE=HexColor('#E9F3F2');GRAY=HexColor('#4D626C');
st=getSampleStyleSheet(); st.add(ParagraphStyle(name='Cover',fontName='DejaVuB',fontSize=24,leading=34,textColor=NAVY,spaceAfter=16));st.add(ParagraphStyle(name='Sub',fontName='DejaVuB',fontSize=15,leading=21,textColor=TEAL,spaceBefore=14,spaceAfter=8));st.add(ParagraphStyle(name='TinyCustom',fontName='DejaVu',fontSize=8.3,leading=13,spaceAfter=7));st.add(ParagraphStyle(name='TableHeaderCustom',fontName='DejaVuB',fontSize=8.2,leading=12,textColor=white));st.add(ParagraphStyle(name='SmallHead',fontName='DejaVuB',fontSize=10.5,leading=15,spaceBefore=11,spaceAfter=5,textColor=NAVY));st.add(ParagraphStyle(name='Note',fontName='DejaVu',fontSize=8.5,leading=12,textColor=GRAY,spaceAfter=8));
doc=SimpleDocTemplate(str(P/'report/Track_A_Findings.pdf'),pagesize=A4,rightMargin=38,leftMargin=38,topMargin=48,bottomMargin=42)
S=[]
def p(text,style='TinyCustom'):S.append(Paragraph(text,st[style]))
def heading(text):p(text,'Sub')
def table(rows,widths=None):
 data=[[Paragraph(str(t).replace('&','&amp;').replace('<','&lt;'),st['TableHeaderCustom'] if i==0 else st['TinyCustom']) for t in row] for i,row in enumerate(rows)]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),white),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,PALE]),('GRID',(0,0),(-1,-1),0.25,HexColor('#CCD9DC')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
 S.append(t);S.append(Spacer(1,6))
def read(name):
 with (R/(name+'.csv')).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def simple(name,cols,n=4,ordering=None):
 rows=read(name)
 if ordering:rows=sorted(rows,key=ordering,reverse=True)
 data=[cols]+[[r.get(k,'') or 'N/A' for k in cols] for r in rows[:n]]
 # column widths dynamic based count
 table(data,[520/len(cols)]*len(cols))
p('OLIST E-COMMERCE','Cover');p('BUSINESS INTELLIGENCE  |  TRACK A: SALES TRENDS','Sub')
p('SQL Server 2022 (T-SQL)  •  Excel Dashboard  •  Historical period 2017-01-01 to 2018-08-31','Note')
p('Team: [add team name / members before submission]  |  Project date: November 2026','Note')
heading('Executive summary')
p(f"The source consists of the eight Olist e-commerce CSV files. In-scope purchase records: <b>{Q['scope_all_orders']:,}</b>, delivered orders: <b>{Q['scope_delivered']:,}</b>. Delivered merchandise sales are <b>BRL {Q['scope_sales_brl']:,.2f}</b>, average order value (AOV) <b>BRL {Q['scope_aov_brl']:,.2f}</b>. 2017-11 is the highest-revenue month. These are historical records rather than current business performance.")
heading('Business scenario (Sales Manager)')
p('A retail marketplace sales manager needs an evidence-based view of order demand and merchandise revenue over time. Using the anonymized Olist Brazilian E-Commerce Public Dataset, the team studies purchase cohorts from January 2017 through August 2018. The objective is to distinguish changes driven by order volume from changes driven by the average merchandise value of each order. Management wants to compare the same January-August months across two years, identify high-volume weekdays, investigate days that materially exceed their own calendar-month mean, and understand the category mix during peak months. The team also wants to monitor order-status completeness, compare daily performance with the same weekday one week earlier, and detect differences between early and late portions of a month. Analytical outputs can guide staffing schedules, category planning, reporting checks, and capacity reviews. The project does not claim to measure marketplace profit, advertising return, or causal effects: Olist contains purchase and item data but not the necessary cost or campaign measures. Recommendations are proposed follow-up investigations, not assumed successes. The Excel dashboard allows the manager to select year and month while recalculating delivered-order totals, merchandise sales, average order value, and sales per calendar day from SQL-derived daily data.')
heading('Methods, scope and integrity checks')
p('Delivered-order merchandise sales = SUM(order_items.price), excluding freight, calculated after joining items to delivered orders. AOV = delivered merchandise sales / count of distinct delivered orders. All dates are based on purchase timestamp. Calendar-day daily averages include zero-sales dates. Status analysis includes all statuses, whereas all other sales analyses use delivered orders. Payment and review records are summarized by order before joining; review scoring selects one valid review/order. No missing-value rows were dropped en masse.')
table([['Evidence / validation check','Value'],['Source order rows',f"{Q['source_rows']['orders']:,}"],['Source item rows',f"{Q['source_rows']['order_items']:,}"],['Scope orders (all statuses)',f"{Q['scope_all_orders']:,}"],['Scope delivered orders',f"{Q['scope_delivered']:,}"],['Delivered orders missing item row',str(Q['missing_items_delivered'])],['Delivered orders without valid review',str(Q['delivered_without_valid_review'])],['Delivered orders without payment',str(Q['delivered_without_payment'])],['Orders with multiple review rows',str(Q['review_orders_multiple_rows'])]],[330,190]);
p('Evidence generated directly from original CSV rows with local SQLite checks and archived in results/*.csv and results/validation_summary.json. SQL Server T-SQL requires final execution/validation in SSMS; no SQL Server instance is available in this environment.','Note')
heading('12 research questions: results, insight and action')
# individual records with reference and compact representative tables
p('G1 — How many orders were placed and what is their status?','SmallHead')
simple('G1_status',['status','orders','percent_all_orders'],8,ordering=lambda r:int(r['orders']))
p('Insight: delivered orders dominate the purchase-date snapshot. Status percentages use all 99,092 in-scope orders as their denominator, not the delivered-only subset. Action: maintain a separate incomplete/canceled-order monitoring view. Limit: order_status is a snapshot, not the sequence of transitions. SQL: G1 in sql/03_analysis.sql.')
p('G2 — How do sales change month to month?','SmallHead')
simple('G2_monthly',['month','delivered_orders','sales_brl','growth_pct'],5,ordering=lambda r:float(r['sales_brl']))
p('Insight: November 2017 leads the historical months (BRL 987,765.37 from 7,289 delivered orders). Monthly growth is not reported for the first month. Action: flag peak months for operations and inventory planning, comparing month-over-month order count and AOV alongside sales. SQL: G2.')
p('G3 — Which delivered orders have missing review or payment records?','SmallHead')
simple('G3_coverage',['month','delivered_orders','without_valid_review','without_payment'],4,ordering=lambda r:int(r['without_valid_review']))
p(f"Insight: {Q['delivered_without_valid_review']:,} delivered orders lack a selected valid review; none lacked a payment row. Action: review outreach/coverage tracking. Limit: missing reviews cannot be treated as negative scores. SQL: G3.")
p('A1 — Sales comparison: Jan-Aug 2017 versus Jan-Aug 2018','SmallHead')
simple('A1_year_comparison',['year','jan_aug_orders','jan_aug_sales_brl','jan_aug_aov_brl'],2)
p('Insight: same-month sales are 141.13% higher in Jan-Aug 2018; average order value is similar (BRL 136.08 versus BRL 136.75), suggesting the increase is primarily due to greater order volume. Action: validate capacity scaling; this does not prove the reason for growth. SQL: A1.')
p('A2 — Which weekdays are busiest?','SmallHead')
simple('A2_weekdays',['weekday','calendar_days','delivered_orders','sales_per_day_brl'],7)
p('Insight: Monday has the highest merchandise sales per calendar weekday (BRL 24,888.55/day across 87 Mondays). Action: examine Monday order-processing staffing using per-day rather than only period totals. SQL: A2.')
p('A3 — Which dates exceed their own monthly daily average?','SmallHead')
simple('A3_above_monthly_daily_average',['date','sales_brl','month_daily_average_brl','difference_brl'],5,ordering=lambda r:float(r['difference_brl']))
p('Insight: exceptional revenue days can be isolated relative to their own month instead of a whole-period baseline. Action: investigate timing and category mixes on high-deviation dates. Limit: the comparison is descriptive and includes zero-sales calendar dates in the month average. SQL: A3.')
S.append(PageBreak())
p('A4 — What categories sold during the three highest-sales months?','SmallHead')
simple('A4_top_month_categories',['month','category','sales_brl','share_of_month_pct'],7,ordering=lambda r:float(r['sales_brl']))
p('Insight: 2017-11, 2018-05 and 2018-04 are the three highest-revenue months. Product categories are allocated at item row grain, avoiding duplicates from other one-to-many tables. Action: inspect whether peak-month category capacity can be supported. SQL: A4.')
p('A5 — How did the order-status mix vary by purchase month?','SmallHead')
simple('A5_status_mix',['month','all_orders','delivered_pct','canceled_pct','other_pct'],5,ordering=lambda r:r['month'])
p('Insight: delivered percentage changes between purchase months; purchase timing matters because orders near the end of the dataset can have unfinished outcomes. Action: monitor status definitions consistently; do not infer the complete status history. SQL: A5.')
p('A6 — Day versus the same weekday seven days earlier','SmallHead')
simple('A6_week_over_week',['date','sales_brl','sales_7days_before_brl','change_pct'],5,ordering=lambda r:abs(float(r['change_brl'])) if r['change_brl'] else -1)
p('Insight: seven-day comparison keeps weekday aligned but may show large percent changes when the previous baseline is very small; zero or absent baselines produce NULL. Action: investigate material absolute gaps alongside percentages. SQL: A6.')
p('A7 — First 15 days vs last days of a month','SmallHead')
simple('A7_half_month',['month','period','calendar_days','sales_per_day_brl'],6)
p('Insight: the two halves have different lengths, so the primary fair comparison is sales per actual calendar day. Action: use the month-half pattern to schedule workload reviews; not every month will show the same direction. SQL: A7.')
p('O1 — Which quarters have the largest within-quarter monthly sales range?','SmallHead')
simple('O1_quarter_stability',['quarter','months_observed','mean_monthly_sales_brl','range_brl'],6)
p('Purpose: compare month-to-month instability for capacity planning; measures are monthly min, max, range and count. The 2018-Q3 observation has only July-August, so compare its range cautiously with complete quarters. SQL: O1.')
p('O2 — Does weekday sales intensity differ from weekend sales?','SmallHead')
simple('O2_weekend_weekday',['day_type','calendar_days','sales_per_day_brl','orders_per_day','aov_brl'],2)
p('Insight: weekdays average BRL 23,405.34/day versus BRL 17,339.34/day on weekends, with similar AOVs. Action: examine weekday capacity demand, not just total sales that differ due to weekday counts. SQL: O2.')
S.append(PageBreak());heading('Six principal findings')
findings=[
 f"In the purchase-date window, {Q['scope_delivered']:,} delivered orders generated BRL {Q['scope_sales_brl']:,.2f} merchandise revenue (G1).",
 'Jan-Aug 2018 sales were 141.13% higher than Jan-Aug 2017, mainly alongside order-volume growth rather than higher AOV (A1).',
 'November 2017 was the strongest month with BRL 987,765.37 merchandise revenue (G2).',
 'Monday ranked highest in average sales per calendar weekday at BRL 24,888.55/day (A2).',
 f"Of delivered orders, {Q['delivered_without_valid_review']:,} had no valid analysis review, while none had missing payment records (G3).",
 'Weekday average sales intensity exceeded weekend average: BRL 23,405.34 versus BRL 17,339.34 per calendar day (O2).']
for i,t in enumerate(findings,1):p(f'<b>{i}.</b> {t}')
heading('Three prioritized business recommendations')
recs=[('Priority 1 — Sales &amp; operations management','Review staffing and fulfillment capacity on Mondays and high-volume weekdays.','A2, O2','Track delivered orders per calendar day and backlog by weekday before/after process changes.'),
 ('Priority 2 — Commercial planning','Review category mix from November 2017, May and April 2018 before similar historical seasonal peaks.','G2, A4','Compare category availability and delivered merchandise sales contribution in later comparable periods.'),
 ('Priority 3 — BI/data quality owner','Audit missing valid review coverage and monitor order-status distribution by purchase month.','G3, A5','Track counts and rates of valid reviewed orders and unresolved statuses by month.')]
for title_,what,refs,measure in recs:
 p(title_,'SmallHead');p(f'<b>Action:</b> {what} <b>Evidence:</b> {refs}. <b>Measure:</b> {measure}')
heading('Limitations / assumptions')
p('This dataset is a 2016-2018 historical snapshot. Comparisons do not prove causation, profitability, future customer demand, campaign impact, or business ROI. The window ends with purchases on 2018-08-31; outcomes can occur later. Status is final snapshot, not event history. Merchandise sales exclude freight. Empty/zero baselines are treated as NULL where a percentage cannot be computed. Quarter 2018-Q3 is incomplete. Cross-system differences should be reconciled after importing to SQL Server 2022.')
heading('Contribution and reference')
p('Team contribution statement: [To be completed accurately by the team: member names, SQL, data validation, report, dashboard, testing, presentation]. All members should be able to explain each query and recompute the dashboard KPIs.')
p('Source: Olist Brazilian E-Commerce Public Dataset, https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce (listed license CC BY-NC-SA 4.0). Tools: SQL Server 2022 T-SQL scripts; local source-data cross-check using SQLite; Excel workbook generated with artifact_tool; Python csv/reportlab for supporting exports. All conclusions rely on original Olist data, not synthetic examples.')
def page(canvas,doc):
 canvas.setStrokeColor(TEAL);canvas.line(38,A4[1]-32,A4[0]-38,A4[1]-32)
 canvas.setFont('DejaVu',8);canvas.setFillColor(GRAY);canvas.drawString(38,26,'OLIST  |  BUSINESS INTELLIGENCE  |  TRACK A')
 canvas.drawRightString(A4[0]-38,26,f'Page {doc.page}')
doc.build(S,onFirstPage=page,onLaterPages=page)
print('report ready', (P/'report/Track_A_Findings.pdf').stat().st_size)
