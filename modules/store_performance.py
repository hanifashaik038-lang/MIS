import pandas as pd
from sqlalchemy import select, func
from database.schema import StockEvent, Store, SKU
from modules.inventory import stock_balance
from utils.calculations import performance_score

def store_kpis(session):
    balances={(r.store_id,r.sku_id):int(r.stock or 0) for r in stock_balance(session)}
    rows=[]
    for store in session.scalars(select(Store)).all():
        ev=session.execute(select(StockEvent).where(StockEvent.store_id==store.id)).scalars().all()
        sold=sum(-e.quantity_delta for e in ev if e.event_type=="SALE")
        rev=sum((-e.quantity_delta)*session.get(SKU,e.sku_id).selling_price for e in ev if e.event_type=="SALE")
        stockouts=sum(1 for (sid,_),v in balances.items() if sid==store.id and v<=0)
        skus=sum(1 for s in session.scalars(select(SKU)).all())
        avail=1-stockouts/max(skus,1)
        opening=sum(e.quantity_delta for e in ev if e.event_type=="OPENING")
        receipts=sum(e.quantity_delta for e in ev if e.event_type=="RECEIPT")
        turnover=sold/max((opening+receipts)/2,1)
        score=performance_score(min(rev/250000,1),avail,min(turnover,12),.82,.85)
        rows.append({"Store":store.name,"Region":store.region,"Revenue":round(rev,2),"Units Sold":sold,"Stockout SKUs":stockouts,"Availability %":round(avail*100,1),"Turnover":round(turnover,2),"Performance Score":score})
    return pd.DataFrame(rows).sort_values("Performance Score",ascending=False)
