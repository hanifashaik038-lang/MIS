from datetime import date, timedelta
from database.schema import PurchaseOrder, StockEvent
from modules.inventory import record_event
import uuid

def create_po(session, store_id, sku, qty):
    po=PurchaseOrder(po_number="PO-"+uuid.uuid4().hex[:8].upper(),store_id=store_id,supplier_id=sku.supplier_id,sku_id=sku.id,quantity=int(qty),expected_date=(date.today()+timedelta(days=3)).isoformat(),status="Open")
    session.add(po); session.commit(); return po

def receive_po(session, po, qty):
    remaining=po.quantity-po.received_qty
    if qty<=0 or qty>remaining: raise ValueError(f"Receipt must be 1 to {remaining} units")
    record_event(session,po.store_id,po.sku_id,"RECEIPT",qty,actor="receiving-user")
    po.received_qty+=qty; po.status="Received" if po.received_qty==po.quantity else "Partially Received"; session.commit()
    return po
