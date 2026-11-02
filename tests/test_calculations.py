from utils.calculations import risk_band,days_cover,performance_score
def test_risk_bands():
    assert risk_band(.2)=="Low" and risk_band(.5)=="Moderate" and risk_band(.7)=="High" and risk_band(.9)=="Critical"
def test_days_cover():
    assert days_cover(20,10)==2
def test_score_range():
    assert 0 <= performance_score(.8,.9,6,.8,.9) <= 100
