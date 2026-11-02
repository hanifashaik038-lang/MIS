from database.db import Base,engine,get_session
from database.seed_data import seed
from modules.prediction import build_training,train_evaluate
if __name__=="__main__":
    Base.metadata.create_all(engine); s=get_session(); seed(s)
    df=build_training(s); model,metrics=train_evaluate(df)
    print("Synthetic chronological holdout metrics:",metrics)
    if model:
        import joblib, pathlib
        p=pathlib.Path(__file__).parent/"saved_model"; p.mkdir(exist_ok=True)
        joblib.dump(model,p/"stockout_rf.joblib")
    s.close()
