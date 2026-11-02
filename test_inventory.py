import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.db import Base
from database.schema import Store,Category,Supplier,SKU
from modules.inventory import record_event
def test_sale_and_receipt_ledger():
    e=create_engine("sqlite:///:memory:"); Base.metadata.create_all(e); S=sessionmaker(bind=e); s=S()
    st=Store(name="Test",region="R",store_type="Urban"); c=Category(name="Cat"); su=Supplier(name="Sup",lead_time_days=2,on_time_rate=.9)
    s.add_all([st,c,su]); s.flush(); sku=SKU(code="T1",barcode="12345678",name="Test SKU",category_id=c.id,supplier_id=su.id,unit_cost=1,selling_price=2,reorder_level=2,shelf_life_days=30); s.add(sku); s.commit()
    record_event(s,st.id,sku.id,"RECEIPT",10); record_event(s,st.id,sku.id,"SALE",3)
    from sqlalchemy import select,func
    assert s.scalar(select(func.sum(__import__("database.schema",fromlist=["StockEvent"]).StockEvent.quantity_delta)))==7
    with pytest.raises(ValueError): record_event(s,st.id,sku.id,"SALE",8)
