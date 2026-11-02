import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def excel_bytes(df):
    b=io.BytesIO()
    with pd.ExcelWriter(b,engine="openpyxl") as w: df.to_excel(w,index=False,sheet_name="Report")
    return b.getvalue()

def pdf_bytes(title, df):
    b=io.BytesIO(); c=canvas.Canvas(b,pagesize=letter); width,height=letter
    c.setFont("Helvetica-Bold",15); c.drawString(40,height-45,title)
    c.setFont("Helvetica",7); y=height-70
    headers=list(df.columns)[:7]; c.drawString(40,y," | ".join(map(str,headers))[:130]); y-=15
    for _,row in df.head(35).iterrows():
        c.drawString(40,y," | ".join(str(row[h])[:20] for h in headers)[:130]); y-=12
        if y<45: c.showPage(); y=height-45
    c.save(); return b.getvalue()
