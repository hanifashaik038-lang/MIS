import random, math
from datetime import date, timedelta, datetime
import numpy as np
import pandas as pd
from sqlalchemy import select
from .schema import Store, Category, Supplier, SKU, StockEvent

CATEGORIES = ["Dairy","Beverages","Packaged Foods","Snacks","Personal Care","Home Care","Staples","Frozen Foods","Bakery","Household Essentials"]
PRODUCTS = [
("Milk 1L","Dairy",32,48,2),("Butter 500g","Dairy",180,230,4),("Bread 400g","Bakery",28,42,2),
("Mineral Water 1L","Beverages",8,15,3),("Orange Juice 1L","Beverages",65,92,5),("Potato Chips 100g","Snacks",18,30,4),
("Instant Noodles","Packaged Foods",10,18,5),("Cooking Oil 1L","Staples",110,145,6),("Shampoo 180ml","Personal Care",95,139,7),
("Laundry Detergent 1kg","Home Care",105,149,7),("Biscuits 200g","Snacks",22,35,5),("Rice 5kg","Staples",260,340,8)]
def seed(session):
    if session.scalar(select(Store.id).limit(1)): return
    random.seed(17); np.random.seed(17)
    stores = [Store(name=f"FreshMart {n}", region=["Hyderabad Central","Cyberabad","Secunderabad","West Hyderabad"][i%4], store_type=["Urban","Residential","Urban","Residential"][i%4]) for i,n in enumerate(["Hyderabad","Secunderabad","Kukatpally","Gachibowli","Miyapur","Madhapur","LB Nagar","Kondapur"])]
    cats=[Category(name=x) for x in CATEGORIES]
    sups=[Supplier(name=f"Supplier {i+1:02}",lead_time_days=random.randint(2,7),on_time_rate=round(random.uniform(.78,.98),2)) for i in range(18)]
    session.add_all(stores+cats+sups); session.flush()
    products=[]
    for i in range(120):
        if i < len(PRODUCTS):
            name,cat,cost,price,life=PRODUCTS[i]
        else:
            cat=CATEGORIES[i%len(CATEGORIES)]; name=f"{['Premium','Family Pack','Classic','Daily'][i%4]} {cat} Item {i+1:03}"
            cost=random.randint(12,250); price=round(cost*random.uniform(1.18,1.45),2); life=random.choice([7,14,30,90,180,365])
        products.append(SKU(code=f"FMCG{i+1:03}",barcode=f"890100{i+1:06}",name=name,category_id=next(c.id for c in cats if c.name==cat),supplier_id=sups[i%len(sups)].id,unit_cost=cost,selling_price=price,reorder_level=random.randint(15,55),shelf_life_days=life))
    session.add_all(products); session.flush()
    # 180 days of daily synthetic demand; initial stock plus daily sales / periodic receipts.
    start=date.today()-timedelta(days=180)
    for st in stores:
        for p in products:
            avg=random.uniform(2,18)*(1.25 if st.store_type=="Urban" else 1)
            stock=int(avg*random.uniform(5,12))
            session.add(StockEvent(event_uid=f"seed-open-{st.id}-{p.id}",store_id=st.id,sku_id=p.id,event_type="OPENING",quantity_delta=stock,occurred_at=datetime.combine(start,datetime.min.time()),source="seed"))
            for day in range(180):
                dt=start+timedelta(days=day)
                weekend=1.25 if dt.weekday()>=5 and p.category_id in [2,4,5,10] else 1
                seasonal=1.15 if dt.month in [4,5] and p.category_id==2 else 1
                demand=max(0,int(np.random.poisson(avg*weekend*seasonal)))
                if stock < demand+int(avg*2):
                    receipt=int(avg*random.uniform(5,9))
                    session.add(StockEvent(event_uid=f"seed-rec-{st.id}-{p.id}-{day}",store_id=st.id,sku_id=p.id,event_type="RECEIPT",quantity_delta=receipt,occurred_at=datetime.combine(dt,datetime.min.time()),source="seed"))
                    stock+=receipt
                sold=min(stock,demand); stock-=sold
                if sold:
                    session.add(StockEvent(event_uid=f"seed-sale-{st.id}-{p.id}-{day}",store_id=st.id,sku_id=p.id,event_type="SALE",quantity_delta=-sold,occurred_at=datetime.combine(dt,datetime.min.time())+timedelta(hours=18),source="seed"))
    session.commit()
