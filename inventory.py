import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from database.schema import StockEvent, SKU, Store, AuditLog
from utils.validators import positive_int

def stock_balance(session, store_id=None, sku_id=None):
    q=select(StockEvent.store_id,StockEvent.sku_id,func.sum(StockEvent.quantity_delta).label("stock")).group_by(StockEvent.store_id,StockEvent.sku_id)
    if store_id: q=q.where(StockEvent.store_id==store_id)
    if sku_id: q=q.where(StockEvent.sku_id==sku_id)
    return session.execute(q).all()

def record_event(session, store_id, sku_id, event_type, qty, actor="demo-user", source="app", event_uid=None, allow_negative=False):
    qty=positive_int(qty)
    delta=-qty if event_type=="SALE" or event_type=="DAMAGE" or event_type=="ADJUSTMENT_OUT" else qty
    current=session.scalar(select(func.coalesce(func.sum(StockEvent.quantity_delta),0)).where(StockEvent.store_id==store_id,StockEvent.sku_id==sku_id)) or 0
    if current+delta < 0 and not allow_negative: raise ValueError(f"Insufficient stock. Available: {current}")
    ev=StockEvent(event_uid=event_uid or str(uuid.uuid4()),store_id=store_id,sku_id=sku_id,event_type=event_type,quantity_delta=delta,occurred_at=datetime.now(timezone.utc),source=source)
    session.add(ev); session.add(AuditLog(actor=actor,action=event_type,detail=f"store={store_id}; sku={sku_id}; delta={delta}")); session.commit()
    return ev

def inventory_frame(session):
    rows=stock_balance(session)
    result=[]
    for r in rows:
        sku=session.get(SKU,r.sku_id); store=session.get(Store,r.store_id)
        if sku and store:
            result.append({"Store":store.name,"store_id":r.store_id,"SKU":sku.code,"sku_id":sku.id,"Product":sku.name,"Stock":int(r.stock or 0),"Reorder Level":sku.reorder_level,"Unit Cost":sku.unit_cost,"Value":round((r.stock or 0)*sku.unit_cost,2)})
    return result
