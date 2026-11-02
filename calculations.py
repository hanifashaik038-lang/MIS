def risk_band(p):
    if p <= .30: return "Low"
    if p <= .60: return "Moderate"
    if p <= .80: return "High"
    return "Critical"

def days_cover(stock, avg_daily):
    return float("inf") if avg_daily <= 0 else max(stock,0)/avg_daily

def performance_score(sales, availability, turnover, forecast, replenishment):
    # Configurable management score; not an industry standard.
    turnover_norm=min(max(turnover/12,0),1)
    return round(100*(.30*sales + .25*availability + .20*turnover_norm + .15*forecast + .10*replenishment),1)
