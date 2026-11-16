import csv,math
from pathlib import Path
from artifact_tool import Workbook,SpreadsheetFile
P=Path('/mnt/data/Track_A_Olist_Sales'); R=P/'results'
def read(name):
 with (R/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:return list(csv.reader(f))
wb=Workbook.create(); dash=wb.worksheets.add('Dashboard'); calc=wb.worksheets.add('Calculations'); data=wb.worksheets.add('SQL_Daily'); monthly=wb.worksheets.add('SQL_Monthly'); ins=wb.worksheets.add('Insights'); help=wb.worksheets.add('Read_Me');rec=wb.worksheets.add('Reconciliation')
navy='#142A3A';teal='#0B8174';lt='#E9F3F2';pale='#F3F6F8';yellow='#EFC46A';muted='#557180'; white='#FFFFFF'
def put(sheet,address,text):sheet.get_range(address).values=[[text]]
def title(sheet,start,end,text):
 sheet.merge_cells(f'{start}:{end}');put(sheet,start,text);sheet.get_range(f'{start}:{end}').format={'fill':navy,'font':{'color':white,'bold':True,'size':18},'row_height':34,'vertical_alignment':'center'}
def head(sheet,rng):sheet.get_range(rng).format={'fill':teal,'font':{'bold':True,'color':white},'row_height':24,'vertical_alignment':'center'}
def table(sheet,source,name,numeric_cols=None):
 lines=read(source); headers=lines[0];rows=[]
 for cells in lines[1:]:
  row=[]
  for i,v in enumerate(cells):
   if numeric_cols and i in numeric_cols:
    try:v=float(v) if '.' in v else int(v)
    except:pass
   row.append(v if v!='' else None)
  rows.append(row)
 sheet.get_range_by_indexes(0,0,len(rows)+1,len(headers)).values=[headers]+rows
 sheet.tables.add(f'A1:{chr(65+len(headers)-1)}{len(rows)+1}',True,name)
 head(sheet,f'A1:{chr(65+len(headers)-1)}1');sheet.freeze_panes.freeze_rows(1)
 sheet.get_range('A:A').format.column_width=17
 for ci in range(1,len(headers)):sheet.get_range(f'{chr(65+ci)}:{chr(65+ci)}').format.column_width=17
 return len(rows)
n=table(data,'Dashboard_daily','DailySQL',set(range(1,8)));nm=table(monthly,'dashboard_monthly','MonthlySQL',{0,1,3,4})
# dashboard layout
for c in 'ABCDEFGHIJKLMNOP':dash.get_range(f'{c}:{c}').format.column_width=12
for col in ['A','D','G','J','M']:dash.get_range(f'{col}:{col}').format.column_width=15
title(dash,'A1','P2','OLIST  /  SALES PERFORMANCE     •     TRACK A')
dash.merge_cells('A3:P3');put(dash,'A3','Purchase cohort: 01 Jan 2017 — 31 Aug 2018   |   Delivered orders only   |   Merchandise BRL, excluding freight')
dash.get_range('A3:P3').format={'font':{'color':muted,'size':10},'row_height':24}
put(dash,'A4','YEAR');put(dash,'D4','MONTH');put(dash,'B4','All');put(dash,'E4','All')
dash.get_range('A4').format.font.bold=True;dash.get_range('D4').format.font.bold=True
for address in ['B4','E4']:
 dash.get_range(address).format={'fill':lt,'font':{'bold':True,'color':navy},'row_height':26,'horizontal_alignment':'center'}
dash.get_range('B4').data_validation={'rule':{'type':'list','values':['All','2017','2018']}}
dash.get_range('E4').data_validation={'rule':{'type':'list','values':['All']+[str(i) for i in range(1,13)]}}
# formula based on SQL_Daily rows, criterion functions to rebuild from totals correctly
last=n+1
def sumcol(col,extra=None):
 rng=f"SQL_Daily!${col}$2:${col}${last}"; yrs=f'SQL_Daily!$B$2:$B${last}';mos=f'SQL_Daily!$C$2:$C${last}'
 cond=[]
 if extra:cond=[f"SQL_Daily!${extra[0]}$2:${extra[0]}${last}",extra[1]]
 def f(year,month):
  args=[rng]
  if year:args += [yrs,'$B$4']
  if month:args += [mos,'$E$4']
  for i in range(0,len(cond),2):args += [cond[i],cond[i+1]]
  return ('SUM('+rng+')') if len(args)==1 else 'SUMIFS('+','.join(args)+')'
 return f'=IF($B$4="All",IF($E$4="All",{f(False,False)},{f(False,True)}),IF($E$4="All",{f(True,False)},{f(True,True)}))'
def addcard(area,label,formula,fmt):
 s,e=area;dash.merge_cells(f'{s}:{e}');put(dash,s,label)
 col=s[0];row=int(s[1:]);dash.merge_cells(f'{col}{row+1}:{e[0]}{int(e[1:])+1}')
 cell=f'{col}{row+1}';dash.get_range(cell).formulas=[[formula]]
 dash.get_range(f'{s}:{e}').format={'fill':navy,'font':{'color':'#C0DBDA','bold':True,'size':11},'row_height':25}
 dash.get_range(f'{col}{row+1}:{e[0]}{int(e[1:])+1}').format={'fill':lt,'font':{'color':navy,'bold':True,'size':19},'row_height':47}
 dash.get_range(cell).set_number_format(fmt)
addcard(('A6','D6'),'MERCHANDISE SALES (BRL)',sumcol('G'),'#,##0.00')
addcard(('E6','H6'),'DELIVERED ORDERS',sumcol('F'),'#,##0')
addcard(('I6','L6'),'AVERAGE ORDER VALUE', '=IFERROR(A7/E7,0)','#,##0.00')
addcard(('M6','P6'),'SALES PER CALENDAR DAY','=IFERROR(A7/'+sumcol('E')[1:]+',0)','#,##0.00')
# supporting dynamic chart data: month of year across selected year, filtered optionally by month
calc.get_range('A1:C1').values=[['Month','Sales_BRL','Orders']]
head(calc,'A1:C1')
for m in range(1,13):
 r=m+1;put(calc,f'A{r}',f'{m:02d}')
 # SUMIFS SQL_Monthly month_no, ignoring selected month unless matches m
 for col,dest in [('E','B'),('D','C')]:
  f1=f'SUMIFS(SQL_Monthly!${col}$2:${col}${nm+1},SQL_Monthly!$B$2:$B${nm+1},{m})'
  f2=f'SUMIFS(SQL_Monthly!${col}$2:${col}${nm+1},SQL_Monthly!$B$2:$B${nm+1},{m},SQL_Monthly!$A$2:$A${nm+1},Dashboard!$B$4)'
  calc.get_range(f'{dest}{r}').formulas=[[f'=IF(AND(Dashboard!$E$4<>"All",Dashboard!$E$4<>{m}),0,IF(Dashboard!$B$4="All",{f1},{f2}))']]
calc.get_range('E1:G1').values=[['Weekday','Sales_BRL','Orders']];head(calc,'E1:G1')
weekdays=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
# helper formulas for other sheet using selector Dashboard B4 E4
def calc_sum(col,excol,exvalue):
 rng=f'SQL_Daily!${col}$2:${col}${last}';yrs=f'SQL_Daily!$B$2:$B${last}';mos=f'SQL_Daily!$C$2:$C${last}';cr=f'SQL_Daily!${excol}$2:${excol}${last}'
 def ff(y,m):
  a=[rng,cr,exvalue]
  if y:a.extend([yrs,'Dashboard!$B$4'])
  if m:a.extend([mos,'Dashboard!$E$4'])
  return 'SUMIFS('+','.join(a)+')'
 return f'=IF(Dashboard!$B$4="All",IF(Dashboard!$E$4="All",{ff(False,False)},{ff(False,True)}),IF(Dashboard!$E$4="All",{ff(True,False)},{ff(True,True)}))'
for i,w in enumerate(weekdays,2):
 put(calc,f'E{i}',w)
 calc.get_range(f'F{i}').formulas=[[calc_sum('G','D',f'E{i}')]]
 calc.get_range(f'G{i}').formulas=[[calc_sum('F','D',f'E{i}')]]
calc.get_range('I1:K1').values=[['Month half','Sales_BRL','Orders']];head(calc,'I1:K1')
for i,name in enumerate(['Days 01-15','Days 16-end'],2):
 put(calc,f'I{i}',name);calc.get_range(f'J{i}').formulas=[[calc_sum('G','H',str(i-1))]];calc.get_range(f'K{i}').formulas=[[calc_sum('F','H',str(i-1))]]
for col in 'ABCDEFGHIJK':calc.get_range(f'{col}:{col}').format.column_width=17
# 3 charts linked to dynamic calc tables
ch1=dash.charts.add('column',calc.get_range('A1:B13'));ch1.title_text='Monthly merchandise sales • BRL';ch1.has_legend=False;ch1.set_position('A11','H27')
ch2=dash.charts.add('bar',calc.get_range('E1:F8'));ch2.title_text='Sales by weekday • BRL';ch2.has_legend=False;ch2.set_position('I11','P27')
ch3=dash.charts.add('column',calc.get_range('I1:J3'));ch3.title_text='Sales by month-half • BRL';ch3.has_legend=False;ch3.set_position('A29','H44')
# chart 4 optional orders per weekday
ch4=dash.charts.add('column',calc.get_range('E1:E8'));ch4.title_text='Order count by weekday';ch4.has_legend=False
# explicit series to avoid using one-only source
a=ch4.series.add('Delivered orders');a.category_formula="'Calculations'!$E$2:$E$8";a.formula="'Calculations'!$G$2:$G$8";ch4.set_position('I29','P44')
dash.merge_cells('A46:P46');put(dash,'A46','FILTERS: Year and month dropdowns above drive all four KPI cards and all charts. Data source: SQL_Daily / SQL_Monthly exports.')
dash.get_range('A46:P46').format={'font':{'color':muted,'size':10},'row_height':28}
dash.merge_cells('A48:P48');put(dash,'A48','UNFILTERED BASELINE INSIGHTS  •  see Insights sheet for query evidence and limitations')
dash.get_range('A48:P48').format={'fill':navy,'font':{'color':white,'bold':True},'row_height':28}
# insights
ins.get_range('A1:E1').values=[['Question','Finding / Action','Evidence','Decision / Owner','Limit / follow up']];head(ins,'A1:E1')
ins.get_range('A2:E7').values=[
 ['G1','96,211 delivered orders within scope','G1_delivered_summary.csv','Sales manager: monitor delivered order mix','Order-status snapshot is not a timeline'],
 ['G2','Highest sales month: 2017-11','G2_monthly.csv','Plan seasonal capacity before high-volume periods','Historical 2017-2018 snapshot only'],
 ['A1','Jan-Aug 2018 sales up 141.13% over Jan-Aug 2017','A1_year_comparison.csv','Review acquisition and capacity needs','Not evidence of causation or current-year trend'],
 ['A2','Monday highest sales per calendar weekday','A2_weekdays.csv','Review Monday order-processing capacity','Compare normalized by calendar-day counts'],
 ['G3','643 delivered orders lacked a valid review','G3_coverage.csv','Improve review-collection monitoring','Missing review is not zero satisfaction'],
 ['A4','Top revenue months: Nov 2017, May/Apr 2018','A4_top_month_categories.csv','Inspect category contributors before planning','Top-month selection based on delivered merchandise sales']]
for col,width in zip('ABCDE',[14,54,30,43,46]):ins.get_range(f'{col}:{col}').format.column_width=width
ins.get_range('A2:E7').format.wrap_text=True;ins.get_range('A2:E7').format.row_height=40
# help
help.get_range('A1:B1').values=[['Track A • Olist Sales','Dashboard usage / definitions']];head(help,'A1:B1')
help.get_range('A2:B13').values=[
 ['Scope','Purchase dates 2017-01-01 inclusive to 2018-09-01 exclusive'],
 ['Source','Olist Brazilian E-Commerce Public Dataset (Kaggle)'],
 ['Attribution','https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce'],
 ['Grain','SQL_Daily: 1 calendar date; SQL_Monthly: 1 purchase month'],
 ['Year filter','Dashboard!B4 → All, 2017, 2018'],
 ['Month filter','Dashboard!E4 → All, 1..12'],
 ['Effect','Both dropdowns affect all four KPIs, 3 required charts and extra order chart'],
 ['Sales','SUM(price) by delivered orders; excludes freight; BRL'],
 ['Orders','Count of distinct delivered order_id (each dated exactly once)'],
 ['AOV','Filtered merchandise sales / filtered delivered orders'],
 ['Sales/day','Filtered merchandise sales / number of matching calendar dates'],
 ['Refresh','Run sql/04_dashboard_exports.sql in SSMS; replace SQL_Daily and SQL_Monthly table values from exported CSV; preserve formulas/columns']]
help.get_range('A:A').format.column_width=24;help.get_range('B:B').format.column_width=110
# Recon: unfiltered base values from daily CSV
v=read('Dashboard_daily')[1:];s=round(sum(float(x[6]) for x in v),2);orders=sum(int(x[5]) for x in v);nd=len(v)
rec.get_range('A1:D1').values=[['KPI','SQL export baseline','Dashboard formula at All/All','Difference']];head(rec,'A1:D1')
recs=[['Sales (BRL)',s,'=Dashboard!A7','=C2-B2'],['Delivered orders',orders,'=Dashboard!E7','=C3-B3'],['AOV (BRL)',s/orders,'=Dashboard!I7','=C4-B4'],['Sales per calendar day',s/nd,'=Dashboard!M7','=C5-B5']]
rec.get_range('A2:D5').values=[[x[0],x[1],None,None] for x in recs]
for i,r in enumerate(recs,2):rec.get_range(f'C{i}:D{i}').formulas=[[r[2],r[3]]]
for col,width in zip('ABCD',[32,24,28,21]):rec.get_range(f'{col}:{col}').format.column_width=width
# some number formats
for area in ['B2:C13','F2:G8','J2:K3']:calc.get_range(area).set_number_format('#,##0.00')
# Export
output=P/'dashboard/Track_A_Sales_Dashboard.xlsx'
SpreadsheetFile.export_xlsx(wb).save(str(output))
print('Workbook exported',output,output.stat().st_size)
try:
 img=wb.render({'sheet_name':'Dashboard','range':'A1:P28','scale':1.4});img.save(str(P/'dashboard/dashboard_preview.png'));print('Rendered preview')
except Exception as e: print('Render warning',str(e)[:240])
