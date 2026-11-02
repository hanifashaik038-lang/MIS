import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import select
from database.db import Base, engine, get_session
from database.schema import Store, SKU, Category, Supplier, Alert, PurchaseOrder
from database.seed_data import seed
from modules.inventory import inventory_frame, record_event
from modules.prediction import current_predictions, build_training, train_evaluate
from modules.alerts import generate_alerts
from modules.procurement import create_po, receive_po
from modules.store_performance import store_kpis
from modules.reporting import excel_bytes, pdf_bytes
from utils.validators import validate_barcode

st.set_page_config(page_title="StockSense AI | FreshMart",page_icon="📦",layout="wide")
st.markdown('''<style>
.stApp{background:#081321;color:#e8f1f8}.block-container{padding-top:1.2rem}
[data-testid="stSidebar"]{background:#101f30}
div[data-testid="stMetric"]{background:#12283a;border:1px solid #1e5360;padding:15px;border-radius:12px}
h1,h2,h3{color:#e9f5f7}.stButton>button{background:#0f9d94;color:white;border:0;border-radius:8px}
.smallmuted{color:#9eb6c5}
</style>''',unsafe_allow_html=True)
Base.metadata.create_all(engine)
s=get_session(); seed(s)
st.sidebar.markdown("# 📦 StockSense AI")
st.sidebar.caption("FreshMart Supermarkets")
st.sidebar.warning("DEMO DATA – SIMULATED FRESHMART OPERATIONS")
role=st.sidebar.selectbox("Demonstration role",["Head Office","Regional Manager","Store Manager","Store Employee"])
pages=["Executive Dashboard","Stockout Prediction","Stockout Alerts","Inventory Management","Barcode Scanner","Purchase Orders & Receiving","Store Performance","Product Analytics","Supplier Analytics","Reports","System Design & Waterfall"]
page=st.sidebar.radio("Navigation",pages)
stores=s.scalars(select(Store)).all(); skus=s.scalars(select(SKU)).all()
pred=current_predictions(s); perf=store_kpis(s)
st.title("StockSense AI")
st.caption("Seven-day stockout intelligence • Inventory control • Store performance")
if page=="Executive Dashboard":
    inv=inventory_frame(s); totalstock=sum(x["Stock"] for x in inv); sales=int(perf["Units Sold"].sum())
    risk=pred[pred.Risk.isin(["High","Critical"])]
    a,b,c,d,e=st.columns(5)
    a.metric("Stores",len(stores)); b.metric("SKUs",len(skus)); c.metric("Units on hand",f"{totalstock:,}"); d.metric("Historical units sold",f"{sales:,}"); e.metric("At-risk pairs",len(risk))
    f,g,h=st.columns(3); f.metric("Current zero-stock pairs",sum(x["Stock"]<=0 for x in inv)); g.metric("Mean risk estimate",f'{pred.Probability.mean()*100:.1f}%'); h.metric("Top store score",f'{perf.iloc[0]["Performance Score"]:.1f}/100')
    c1,c2=st.columns(2)
    c1.plotly_chart(px.bar(perf,x="Store",y="Revenue",title="Store sales revenue",template="plotly_dark"),use_container_width=True)
    c2.plotly_chart(px.histogram(pred,x="Risk",color="Risk",title="Seven-day risk distribution",template="plotly_dark"),use_container_width=True)
    st.subheader("Highest-risk product / store combinations")
    st.dataframe(pred.sort_values("Probability",ascending=False).head(15),use_container_width=True,hide_index=True)
    st.subheader("Store performance")
    st.dataframe(perf,use_container_width=True,hide_index=True)
elif page=="Stockout Prediction":
    st.subheader("Seven-day stockout probability")
    st.info("Prediction horizon: the next 7 days. Values shown here are transparent rule-based baseline estimates; the training pipeline below evaluates a time-split Random Forest on synthetic historical examples. Baseline values are not ML predictions.")
    store_filter=st.selectbox("Store",["All"]+[x.name for x in stores]); risk_filter=st.multiselect("Risk level",["Low","Moderate","High","Critical"],default=["Moderate","High","Critical"])
    view=pred.copy()
    if store_filter!="All": view=view[view.Store==store_filter]
    if risk_filter: view=view[view.Risk.isin(risk_filter)]
    st.dataframe(view.sort_values("Probability",ascending=False),use_container_width=True,hide_index=True)
    st.subheader("Train and evaluate model on simulated history")
    if st.button("Train Random Forest and show holdout metrics"):
        with st.spinner("Building time-ordered training examples…"):
            df=build_training(s); model,metrics=train_evaluate(df)
        if model is None: st.warning("Not enough varied training examples to train a reliable model. Baseline estimates remain in use.")
        else:
            st.success("Model trained for this session only. Metrics are on the later chronological holdout.")
            st.json({k:v for k,v in metrics.items() if k!="confusion_matrix"})
            st.write("Confusion matrix (actual rows × predicted columns):",metrics["confusion_matrix"])
elif page=="Stockout Alerts":
    st.subheader("Stockout detection and alerts")
    if st.button("Run detection and deduplicate alerts"):
        st.success(f"Created {generate_alerts(s,pred)} new alert(s). Existing unresolved alerts were not duplicated.")
    alerts=s.scalars(select(Alert).order_by(Alert.created_at.desc())).all()
    if alerts:
        for al in alerts:
            sku=s.get(SKU,al.sku_id); store=s.get(Store,al.store_id)
            with st.expander(f'{al.severity} · {sku.name} · {store.name} · {al.status}'):
                st.write(al.message,f"Risk estimate: {al.probability:.1%}")
                status=st.selectbox("Update status",["Open","Acknowledged","Assigned","Resolved","Closed"],index=["Open","Acknowledged","Assigned","Resolved","Closed"].index(al.status),key=f"al{al.id}")
                if st.button("Save status",key=f"save{al.id}"): al.status=status; s.commit(); st.rerun()
    else: st.info("No alerts yet. Run detection to evaluate current stock and risk.")
elif page=="Inventory Management":
    st.subheader("Store inventory and immutable stock ledger")
    inv=pd.DataFrame(inventory_frame(s)); store=st.selectbox("Filter store",["All"]+[x.name for x in stores])
    if store!="All": inv=inv[inv.Store==store]
    st.dataframe(inv,use_container_width=True,hide_index=True)
    st.caption("Stock is derived by summing append-only stock events; corrections are new adjustment events.")
    st.subheader("Record stock adjustment")
    with st.form("adjust"):
        stid=st.selectbox("Store",stores,format_func=lambda x:x.name); sku=st.selectbox("Product",skus,format_func=lambda x:f"{x.code} · {x.name}")
        typ=st.selectbox("Adjustment",["ADJUSTMENT_IN","ADJUSTMENT_OUT","DAMAGE"]); qty=st.number_input("Quantity",1,100000,1)
        ok=st.form_submit_button("Post adjustment")
        if ok:
            try: record_event(s,stid.id,sku.id,typ,int(qty)); st.success("Stock event recorded.")
            except Exception as ex: st.error(str(ex))
elif page=="Barcode Scanner":
    st.subheader("Barcode scan / sale processing")
    st.caption("USB keyboard-wedge scanners can type into the barcode field. Manual entry is supported.")
    barcode=st.text_input("Scan or enter barcode")
    qty=st.number_input("Quantity",1,1000,1)
    if st.button("Identify product"):
        try:
            code=validate_barcode(barcode); sku=s.scalar(select(SKU).where(SKU.barcode==code))
            if not sku: st.error("Unknown barcode. Check the code or add the SKU to master data.")
            else: st.session_state["scan_sku"]=sku.id; st.success(f"Found {sku.name} ({sku.code})")
        except Exception as ex: st.error(str(ex))
    if "scan_sku" in st.session_state:
        store=st.selectbox("Store for sale",stores,format_func=lambda x:x.name)
        if st.button("Confirm sale and deduct stock"):
            try: record_event(s,store.id,st.session_state["scan_sku"],"SALE",int(qty)); st.success("Sale posted; inventory updated.")
            except Exception as ex: st.error(str(ex))
elif page=="Purchase Orders & Receiving":
    st.subheader("Purchase orders")
    with st.form("po"):
        store=st.selectbox("Destination store",stores,format_func=lambda x:x.name); sku=st.selectbox("SKU",skus,format_func=lambda x:f"{x.code} · {x.name}"); qty=st.number_input("Order quantity",1,100000,50)
        if st.form_submit_button("Create purchase order"):
            po=create_po(s,store.id,sku,int(qty)); st.success(f"Created {po.po_number}")
    orders=s.scalars(select(PurchaseOrder).order_by(PurchaseOrder.id.desc())).all()
    for po in orders:
        sku=s.get(SKU,po.sku_id); store=s.get(Store,po.store_id)
        with st.expander(f"{po.po_number} · {sku.name} · {store.name} · {po.status}"):
            st.write(f"Ordered {po.quantity} · received {po.received_qty} · expected {po.expected_date}")
            q=st.number_input("Receive quantity",1,max(1,po.quantity-po.received_qty),1,key=f"rc{po.id}")
            if st.button("Confirm goods receipt",key=f"recv{po.id}"):
                try: receive_po(s,po,int(q)); st.success("Receipt posted to stock ledger."); st.rerun()
                except Exception as ex: st.error(str(ex))
elif page=="Store Performance":
    st.subheader("Store comparison and ranking")
    st.caption("Management score weights: 30% sales, 25% availability, 20% inventory efficiency, 15% forecast accuracy, 10% replenishment efficiency. Configurable illustrative score, not an industry standard.")
    st.plotly_chart(px.bar(perf,x="Store",y="Performance Score",color="Performance Score",template="plotly_dark"),use_container_width=True)
    st.dataframe(perf,use_container_width=True,hide_index=True)
elif page=="Product Analytics":
    st.subheader("Product and category analytics")
    p=pred.merge(pd.DataFrame([{"sku_id":x.id,"Category":s.get(Category,x.category_id).name} for x in skus]),on="sku_id")
    st.plotly_chart(px.bar(p.groupby("Category",as_index=False).agg({"Current Stock":"sum","Avg Daily Sales":"sum"}),x="Category",y=["Current Stock","Avg Daily Sales"],barmode="group",template="plotly_dark"),use_container_width=True)
    st.dataframe(p.sort_values("Avg Daily Sales",ascending=False).head(30),use_container_width=True,hide_index=True)
elif page=="Supplier Analytics":
    st.subheader("Supplier performance")
    data=[]
    for sup in s.scalars(select(Supplier)).all():
        data.append({"Supplier":sup.name,"Average lead time (days)":sup.lead_time_days,"On-time delivery %":round(sup.on_time_rate*100,1),"Indicative fulfilment %":round((sup.on_time_rate*.98)*100,1)})
    st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)
    st.caption("Supplier measures are seeded illustrative attributes; actual PO/ASN delivery history is not connected in this demo.")
elif page=="Reports":
    st.subheader("Download operational reports")
    choices={"Stockout probability":pred,"Inventory":pd.DataFrame(inventory_frame(s)),"Store performance":perf,"Supplier performance":pd.DataFrame([{"Supplier":x.name,"Lead time":x.lead_time_days,"On-time %":x.on_time_rate*100} for x in s.scalars(select(Supplier)).all()])}
    typ=st.selectbox("Report",list(choices)); df=choices[typ]
    st.dataframe(df.head(30),use_container_width=True)
    st.download_button("Download CSV",df.to_csv(index=False).encode(),file_name=f"{typ.lower().replace(' ','_')}.csv",mime="text/csv")
    st.download_button("Download Excel",excel_bytes(df),file_name="stocksense_report.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("Download PDF",pdf_bytes(typ,df),file_name="stocksense_report.pdf",mime="application/pdf")
elif page=="System Design & Waterfall":
    st.subheader("Waterfall delivery and system design")
    st.markdown("**1. Requirements → 2. Design → 3. Implementation → 4. Integration → 5. Testing → 6. Deployment & Maintenance**")
    st.markdown("HLD: Barcode/Web app → Store app + local DB → sync agent → central DB → prediction engine → KPI analytics → dashboard/alerts.")
    st.markdown("This academic demo consolidates the stores into one SQLite database. Offline queue behaviour is represented by unique event IDs and an idempotent central-ingestion module, not a deployed distributed topology.")
    st.markdown("See `docs/` for requirement analysis, design, schema, API contracts, test plan and Waterfall phase deliverables.")
s.close()
