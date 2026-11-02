from sqlalchemy import select
from database.schema import Alert
from utils.calculations import risk_band

def generate_alerts(session, predictions):
    created=0
    for _,r in predictions.iterrows():
        if r["Risk"] not in ["High","Critical"] and r["Current Stock"]>0: continue
        existing=session.scalar(select(Alert).where(Alert.store_id==int(r.store_id),Alert.sku_id==int(r.sku_id),Alert.status.in_(["Open","Acknowledged","Assigned"])))
        if existing: continue
        session.add(Alert(store_id=int(r.store_id),sku_id=int(r.sku_id),severity="Critical" if r["Risk"]=="Critical" or r["Current Stock"]<=0 else "High",probability=float(r["Probability"]),message=f'{r["Product"]}: {r["Action"]}',status="Open")); created+=1
    session.commit(); return created
