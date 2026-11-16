import csv,sqlite3,os,collections,datetime,json,calendar,statistics
from pathlib import Path
P=Path(__file__).resolve().parents[1]; raw=P/'data/raw';out=P/'results'; out.mkdir(exist_ok=True)
db=sqlite3.connect(str(P/'tools/olist_local.sqlite')); c=db.cursor(); c.execute('PRAGMA journal_mode=OFF');c.execute('PRAGMA synchronous=OFF')
files={'customers':'olist_customers_dataset.csv','orders':'olist_orders_dataset.csv','order_items':'olist_order_items_dataset.csv','products':'olist_products_dataset.csv','sellers':'olist_sellers_dataset.csv','order_payments':'olist_order_payments_dataset.csv','order_reviews':'olist_order_reviews_dataset.csv','category_translation':'product_category_name_translation.csv'}
counts={}
for table,name in files.items():
 with (raw/name).open(encoding='utf-8-sig',newline='') as f:
  rdr=csv.reader(f);headers=next(rdr)
  c.execute(f'DROP TABLE IF EXISTS {table}');c.execute(f'CREATE TABLE {table} ({", ".join(chr(34)+h+chr(34)+" TEXT" for h in headers)})')
  insert=f'INSERT INTO {table} VALUES ({",".join("?" for x in headers)})'
  data=list(rdr);c.executemany(insert,data); counts[table]=len(data)
 print(table,counts[table],flush=True)
db.commit()
c.executescript('''CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_pay_order ON order_payments(order_id);
CREATE INDEX IF NOT EXISTS idx_reviews_order ON order_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_purchase_timestamp);''')
START='2017-01-01'; END='2018-09-01'
def write(name,headers,rows):
 with (out/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(headers);w.writerows(rows)
# normalized one-row order state to avoid duplication
q='''SELECT o.order_id,o.customer_id,o.order_status,substr(o.order_purchase_timestamp,1,10) dt,substr(o.order_purchase_timestamp,1,7) month,
 CAST(substr(o.order_purchase_timestamp,1,4) AS int) year,cast(substr(o.order_purchase_timestamp,6,2) AS int) month_no,
 c.customer_unique_id,COALESCE(i.sales,0),i.n_items,COALESCE(pay.n_pay,0),rev.review_score
 FROM orders o LEFT JOIN customers c ON c.customer_id=o.customer_id
 LEFT JOIN (SELECT order_id,SUM(CAST(price AS REAL)) sales,COUNT(*) n_items FROM order_items GROUP BY order_id) i ON i.order_id=o.order_id
 LEFT JOIN (SELECT order_id,COUNT(*) n_pay FROM order_payments GROUP BY order_id) pay ON pay.order_id=o.order_id
 LEFT JOIN (SELECT order_id,review_score FROM (SELECT order_id,review_score,ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY (review_answer_timestamp IS NOT NULL) DESC,review_answer_timestamp DESC,review_creation_date DESC,review_id DESC,rowid DESC) rn FROM order_reviews WHERE CAST(review_score AS int) BETWEEN 1 AND 5) r WHERE rn=1) rev ON rev.order_id=o.order_id
 WHERE o.order_purchase_timestamp>=? AND o.order_purchase_timestamp<?'''
orders=[dict(zip(['id','customer_id','status','date','month','year','mno','unique','sales','items','payments','score'],r)) for r in c.execute(q,(START,END)).fetchall()]
for o in orders:o['sales']=round(o['sales'],2)
delivered=[o for o in orders if o['status']=='delivered']
print('in scope',len(orders),'delivered',len(delivered),flush=True)
bydate=collections.defaultdict(list);bymonth=collections.defaultdict(list)
for o in delivered:bydate[o['date']].append(o);bymonth[o['month']].append(o)
months=[f'{y}-{m:02d}' for y in (2017,2018) for m in range(1,13) if (y==2017 or m<=8)]
dates=[];day=datetime.date(2017,1,1)
while day<datetime.date(2018,9,1):dates.append(day);day+=datetime.timedelta(days=1)
month_data={m:{'sales':round(sum(o['sales'] for o in bymonth[m]),2),'orders':len(bymonth[m])} for m in months}
# G1 status
status_count=collections.Counter(o['status'] for o in orders)
write('G1_status',['status','orders','percent_all_orders'],[(s,n,round(100*n/len(orders),2)) for s,n in sorted(status_count.items())])
write('G1_delivered_summary',['delivered_orders','unique_customers','merchandise_sales_brl','aov_brl','missing_item_orders'],[[len(delivered),len(set(o['unique'] for o in delivered if o['unique'])),round(sum(o['sales'] for o in delivered),2),round(sum(o['sales'] for o in delivered)/len(delivered),2),sum(o['items'] is None for o in delivered)]])
# G2
runs=0;prev=None;g2=[]
for m in months:
 d=month_data[m];runs+=d['sales'];growth=None if not prev or prev['sales']==0 else round(100*(d['sales']/prev['sales']-1),2)
 g2.append((m,d['orders'],d['sales'],round(d['sales']/d['orders'],2) if d['orders'] else None,growth,round(runs,2)));prev=d
write('G2_monthly',['month','delivered_orders','sales_brl','aov_brl','growth_pct','running_sales_brl'],g2)
# G3
r3=[]
for m in months:
 v=bymonth[m]; n=len(v); reviewed=sum(o['score'] is not None for o in v);paid=sum(o['payments']>0 for o in v)
 r3.append([m,n,reviewed,n-reviewed,round(100*reviewed/n,2) if n else None,paid,n-paid,round(100*paid/n,2) if n else None])
write('G3_coverage',['month','delivered_orders','with_valid_review','without_valid_review','review_coverage_pct','with_payment','without_payment','payment_coverage_pct'],r3)
write('G3_missing_sample',['order_id','month','missing_review','missing_payment'],[[o['id'],o['month'],int(o['score'] is None),int(o['payments']==0)] for o in delivered if o['score'] is None or not o['payments']][:30])
# A1
rows=[]
for yr in [2017,2018]:
 v=[o for o in delivered if o['year']==yr and o['mno']<=8];s=round(sum(x['sales'] for x in v),2)
 rows.append([yr,len(v),s,round(s/len(v),2) if v else None])
write('A1_year_comparison',['year','jan_aug_orders','jan_aug_sales_brl','jan_aug_aov_brl'],rows)
# A2 weekday all days
week={i:{'days':0,'orders':0,'sales':0} for i in range(7)}
for d in dates:
 v=bydate[str(d)];t=week[d.weekday()];t['days']+=1;t['orders']+=len(v);t['sales']+=sum(o['sales'] for o in v)
write('A2_weekdays',['weekday_no','weekday','calendar_days','delivered_orders','sales_brl','aov_brl','orders_per_day','sales_per_day_brl'],[[i,calendar.day_name[i],v['days'],v['orders'],round(v['sales'],2),round(v['sales']/v['orders'],2),round(v['orders']/v['days'],3),round(v['sales']/v['days'],2)] for i,v in week.items()])
# A3
month_days=collections.Counter(str(d)[:7] for d in dates)
a3=[]
for d in dates:
 ds=round(sum(o['sales'] for o in bydate[str(d)]),2);mean=month_data[str(d)[:7]]['sales']/month_days[str(d)[:7]]
 if ds>mean:a3.append([str(d),str(d)[:7],ds,round(mean,2),round(ds-mean,2)])
write('A3_above_monthly_daily_average',['date','month','sales_brl','month_daily_average_brl','difference_brl'],a3)
# A4 top3 categories
best=sorted(months,key=lambda m:(-month_data[m]['sales'],m))[:3]
catrows=c.execute('''SELECT substr(o.order_purchase_timestamp,1,7) m,COALESCE(t.product_category_name_english,p.product_category_name,'Uncategorized') cat, SUM(CAST(i.price AS REAL)) sales,COUNT(*) items
 FROM orders o JOIN order_items i ON i.order_id=o.order_id LEFT JOIN products p ON p.product_id=i.product_id LEFT JOIN category_translation t ON t.product_category_name=p.product_category_name
 WHERE o.order_status='delivered' AND o.order_purchase_timestamp>=? AND o.order_purchase_timestamp<? GROUP BY 1,2''',(START,END)).fetchall()
a4=[]
for m,cat,s,n in catrows:
 if m in best:a4.append([m,cat,round(s,2),n,round(100*s/month_data[m]['sales'],3)])
a4.sort(key=lambda x:(-x[2],x[0],x[1]));write('A4_top_month_categories',['month','category','sales_brl','items','share_of_month_pct'],a4)
# A5
allmonths=collections.defaultdict(list)
for o in orders:allmonths[o['month']].append(o)
write('A5_status_mix',['month','all_orders','delivered','canceled','other','delivered_pct','canceled_pct','other_pct'],[[m,len(v),sum(x['status']=='delivered' for x in v),sum(x['status']=='canceled' for x in v),sum(x['status'] not in ('delivered','canceled') for x in v),round(100*sum(x['status']=='delivered' for x in v)/len(v),2) if v else None,round(100*sum(x['status']=='canceled' for x in v)/len(v),2) if v else None,round(100*sum(x['status'] not in ('delivered','canceled') for x in v)/len(v),2) if v else None] for m in months for v in [allmonths[m]]])
# A6
daily={str(d):round(sum(o['sales'] for o in bydate[str(d)]),2) for d in dates}
a6=[]
for d in dates:
 before=d-datetime.timedelta(days=7);now=daily[str(d)];prior=daily.get(str(before));a6.append([str(d),now,prior,round(now-prior,2) if prior is not None else None,round(100*(now/prior-1),2) if prior else None])
write('A6_week_over_week',['date','sales_brl','sales_7days_before_brl','change_brl','change_pct'],a6)
# A7
a7=[]
for m in months:
 y,mo=map(int,m.split('-'));limit=calendar.monthrange(y,mo)[1]
 for segment in (1,2):
  nd=15 if segment==1 else limit-15
  v=[o for o in bymonth[m] if (int(o['date'][-2:])<=15)==(segment==1)]
  s=round(sum(o['sales'] for o in v),2);n=len(v)
  a7.append([m,'Days 01-15' if segment==1 else 'Days 16-end',nd,n,s,round(s/nd,2),round(n/nd,3),round(s/n,2) if n else None])
write('A7_half_month',['month','period','calendar_days','delivered_orders','sales_brl','sales_per_day_brl','orders_per_day','aov_brl'],a7)
# O1 which seasons more stable? month variation; useful for capacity planning
quarter=collections.defaultdict(list)
for m in months:quarter[f'{m[:4]}-Q{(int(m[5:])-1)//3+1}'].append(month_data[m]['sales'])
write('O1_quarter_stability',['quarter','months_observed','total_sales_brl','mean_monthly_sales_brl','min_monthly_sales_brl','max_monthly_sales_brl','range_brl'],[[q,len(v),round(sum(v),2),round(sum(v)/len(v),2),round(min(v),2),round(max(v),2),round(max(v)-min(v),2)] for q,v in sorted(quarter.items())])
# O2 weekend vs weekday comparable per day
forname=[]
for typ,weekdays in [('Weekdays',range(5)),('Weekend',[5,6])]:
 dd=[d for d in dates if d.weekday() in weekdays]; v=[o for d in dd for o in bydate[str(d)]];s=round(sum(o['sales'] for o in v),2)
 forname.append([typ,len(dd),len(v),s,round(s/len(dd),2),round(len(v)/len(dd),3),round(s/len(v),2) if v else None])
write('O2_weekend_weekday',['day_type','calendar_days','delivered_orders','sales_brl','sales_per_day_brl','orders_per_day','aov_brl'],forname)
# dashboard month x weekday summaries at disjoint grain for filters
facts=[]
for d in dates:
 date=str(d);m=date[:7];v=bydate[date];facts.append([date,int(m[:4]),int(m[5:]),calendar.day_name[d.weekday()],1,len(v),round(sum(o['sales'] for o in v),2),1 if d.day<=15 else 2])
write('Dashboard_daily',['date','year','month_no','weekday','calendar_days','delivered_orders','sales_brl','half'],facts)
# month category optional, avoid overlapping for dashboard
write('dashboard_monthly',['year','month_no','month','delivered_orders','sales_brl'],[[int(m[:4]),int(m[5:]),m,month_data[m]['orders'],month_data[m]['sales']] for m in months])
# data quality
quality={'source_rows':counts,'scope_all_orders':len(orders),'scope_delivered':len(delivered),'missing_items_delivered':sum(o['items'] is None for o in delivered),'delivered_without_payment':sum(o['payments']==0 for o in delivered),'delivered_without_valid_review':sum(o['score'] is None for o in delivered),'status_counts':dict(status_count),'scope_sales_brl':round(sum(o['sales'] for o in delivered),2),'scope_aov_brl':round(sum(o['sales'] for o in delivered)/len(delivered),2),'top_3_sales_months':best,'2017_2018_jan_aug_sales_growth_pct':round(100*(rows[1][2]/rows[0][2]-1),2),'month_best_sales':max(months,key=lambda m:month_data[m]['sales']),'week_best_sales_per_calendar_day':calendar.day_name[max(week,key=lambda k:week[k]['sales']/week[k]['days'])]}
for t,key in [('orders','order_id'),('customers','customer_id'),('order_items','order_id'),('products','product_id'),('sellers','seller_id'),('order_payments','order_id')]:
 if t in ('order_items','order_payments'):continue
 quality[f'{t}_duplicate_{key}']=c.execute(f'SELECT COUNT(*)-COUNT(DISTINCT {key}) FROM {t}').fetchone()[0]
quality['orders_without_customer']=c.execute('SELECT COUNT(*) FROM orders o LEFT JOIN customers c ON c.customer_id=o.customer_id WHERE c.customer_id IS NULL').fetchone()[0]
quality['item_without_order']=c.execute('SELECT COUNT(*) FROM order_items i LEFT JOIN orders o ON o.order_id=i.order_id WHERE o.order_id IS NULL').fetchone()[0]
quality['review_orders_multiple_rows']=c.execute('SELECT COUNT(*) FROM (SELECT order_id FROM order_reviews GROUP BY order_id HAVING COUNT(*)>1)').fetchone()[0]
quality['invalid_review_scores']=c.execute('SELECT COUNT(*) FROM order_reviews WHERE review_score IS NULL OR CAST(review_score AS int) NOT BETWEEN 1 AND 5').fetchone()[0]
quality['items_negative_price']=c.execute('SELECT COUNT(*) FROM order_items WHERE CAST(price AS REAL)<0').fetchone()[0]
quality['orders_min_max_purchase']=c.execute('SELECT MIN(order_purchase_timestamp),MAX(order_purchase_timestamp) FROM orders').fetchone()
(P/'results/validation_summary.json').write_text(json.dumps(quality,indent=2),encoding='utf-8')
print(json.dumps(quality,indent=2),flush=True)
db.close()
