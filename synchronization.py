from sqlalchemy import select
from database.schema import StockEvent, SyncLog

def ingest_events(session, batch_uid, events):
    if session.scalar(select(SyncLog).where(SyncLog.batch_uid==batch_uid)):
        return {"accepted":0,"rejected":len(events),"duplicate_batch":True}
    accepted=rejected=0
    for item in events:
        if session.scalar(select(StockEvent.id).where(StockEvent.event_uid==item["event_uid"])):
            rejected+=1; continue
        session.add(StockEvent(event_uid=item["event_uid"],store_id=item["store_id"],sku_id=item["sku_id"],event_type=item["event_type"],quantity_delta=item["quantity_delta"],source="offline-sync",sync_status="synced"))
        accepted+=1
    session.add(SyncLog(batch_uid=batch_uid,accepted=accepted,rejected=rejected)); session.commit()
    return {"accepted":accepted,"rejected":rejected,"duplicate_batch":False}
