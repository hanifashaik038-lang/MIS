import pandas as pd, numpy as np
from sqlalchemy import select, func
from database.schema import StockEvent, SKU, Store, Supplier
from utils.calculations import risk_band, days_cover
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

def historical_daily(session):
    rows=session.execute(select(StockEvent.store_id,StockEvent.sku_id,func.date(StockEvent.occurred_at),func.sum(StockEvent.quantity_delta)).where(StockEvent.event_type=="SALE").group_by(StockEvent.store_id,StockEvent.sku_id,func.date(StockEvent.occurred_at))).all()
    return pd.DataFrame(rows,columns=["store_id","sku_id","day","delta"]).assign(sales=lambda x:-x.delta)

def build_training(session):
    sales=historical_daily(session)
    if sales.empty: return pd.DataFrame()
    sales["day"]=pd.to_datetime(sales.day)
    allrows=[]
    for (store,sku),g in sales.groupby(["store_id","sku_id"]):
        g=g.sort_values("day").set_index("day").asfreq("D",fill_value=0).reset_index()
        vals=g.sales.to_numpy()
        for i in range(21,len(vals)-7):
            hist=vals[max(0,i-14):i]
            future=vals[i:i+7]
            # Demand proxy; target reflects next-seven-day demand exceeding a stock position sampled from recent cover.
            avg=float(np.mean(hist)); stock_proxy=max(0,int(avg*np.random.default_rng(i+sku+store).uniform(1.5,10)))
            allrows.append({"store_id":store,"sku_id":sku,"stock":stock_proxy,"avg_demand":avg,"demand_std":float(np.std(hist)),"trend":float(np.mean(hist[-7:])-np.mean(hist[:-7])) if len(hist)>=14 else 0,"weekday":int(g.day.iloc[i].weekday()),"weekend":int(g.day.iloc[i].weekday()>=5),"lead_time":5,"reorder":max(1,int(avg*3)),"future_demand":float(np.sum(future)),"target":int(stock_proxy < np.sum(future)),"day":g.day.iloc[i]})
    return pd.DataFrame(allrows)

FEATURES=["stock","avg_demand","demand_std","trend","weekday","weekend","lead_time","reorder"]
def train_evaluate(df):
    if len(df)<100 or df.target.nunique()<2: return None, {}
    df=df.sort_values("day"); cut=int(len(df)*.8)
    tr,te=df.iloc[:cut],df.iloc[cut:]
    model=RandomForestClassifier(n_estimators=100,max_depth=9,min_samples_leaf=3,class_weight="balanced",random_state=42,n_jobs=-1)
    model.fit(tr[FEATURES],tr.target)
    pred=model.predict(te[FEATURES]); prob=model.predict_proba(te[FEATURES])[:,1]
    metrics={"accuracy":accuracy_score(te.target,pred),"precision":precision_score(te.target,pred,zero_division=0),"recall":recall_score(te.target,pred,zero_division=0),"f1":f1_score(te.target,pred,zero_division=0),"roc_auc":roc_auc_score(te.target,prob) if te.target.nunique()>1 else None,"confusion_matrix":confusion_matrix(te.target,pred).tolist(),"train_rows":len(tr),"test_rows":len(te)}
    return model,metrics

def current_predictions(session):
    daily=historical_daily(session)
    balances={}
    from modules.inventory import stock_balance
    for r in stock_balance(session): balances[(r.store_id,r.sku_id)]=int(r.stock or 0)
    out=[]
    for (store_id,sku_id),g in daily.groupby(["store_id","sku_id"]):
        sku=session.get(SKU,int(sku_id)); store=session.get(Store,int(store_id)); sup=session.get(Supplier,sku.supplier_id)
        avg=float(g.sort_values("day").tail(28).sales.mean())
        std=float(g.sort_values("day").tail(28).sales.std() or 0)
        stock=balances.get((int(store_id),int(sku_id)),0); lead=sup.lead_time_days
        cover=days_cover(stock,avg)
        # Transparent rule-based baseline, used if model unavailable; never represented as ML.
        base=1/(1+np.exp(-((lead-cover)*0.75 + (std/max(avg,1))*0.15)))
        prob=float(np.clip(base,0,1))
        out.append({"Store":store.name,"store_id":store_id,"SKU":sku.code,"sku_id":sku_id,"Product":sku.name,"Category":sku.category_id,"Current Stock":stock,"Avg Daily Sales":round(avg,2),"Days Cover":round(cover,1) if np.isfinite(cover) else 999,"Lead Time":lead,"Probability":prob,"Risk":risk_band(prob),"Action":"Raise urgent replenishment" if cover<lead else ("Review reorder quantity" if prob>.3 else "Monitor")})
    return pd.DataFrame(out)
