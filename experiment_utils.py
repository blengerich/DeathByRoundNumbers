import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score as aps
from sklearn.metrics import f1_score
from sklearn.metrics import roc_auc_score as auc
from sklearn.model_selection import train_test_split
from interpret.glassbox import ExplainableBoostingClassifier as ebc
from sklearn.neural_network import MLPClassifier
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV

def clip_outliers(df):
    for col in df.columns:
        try:
            df[col] = np.clip(df[col], np.percentile(df[col], 0.1), np.percentile(df[col], 99.9))
        except:
            pass
    return df

def fillna_unknown_dtype_col(X):
    if X.dtype == np.int or X.dtype == np.int64:
        X = X.fillna(value=-1)
    elif X.dtype == np.float:
        X = X.fillna(value=-1)
    elif X.dtype == np.bool:
        X = X.fillna(value=False)
    elif X.dtype == np.object:
        X = X.fillna(value='missing')
    else:
        print(X.dtype)
    return X


def evaluate_model(model, X_train, X_test, Y_train, Y_test):
    def print_metric_result(metric, metric_name, train, proba):
        if train:
            X, Y = X_train, Y_train
            indicator = "Train"
        else:
            X, Y = X_test, Y_test
            indicator = "Test"
        preds = model.predict_proba(X)[:, 1]
        if not proba:
            preds = np.round(preds)
        print(f"{metric_name}\t{indicator}:{metric(Y, preds):.2f}")
    print_metric_result(auc, "AUC", True, True)
    print_metric_result(auc, "AUC", False, True)
    print_metric_result(aps, "APS", True, True)
    print_metric_result(aps, "APS", False, True)
    print_metric_result(f1_score, "F1", True, False)
    print_metric_result(f1_score, "F1", False, False)
    
    
def fit_xgb1(X_train, X_test, Y_train, Y_test):
    xgb = XGBClassifier(max_depth=1, n_estimators=1000)
    xgb.fit(X_train, Y_train)
    evaluate_model(xgb, X_train, X_test, Y_train, Y_test)
    
def fit_xgb2(X_train, X_test, Y_train, Y_test):
    xgb = XGBClassifier(max_depth=2, n_estimators=1000)
    xgb.fit(X_train, Y_train)
    evaluate_model(xgb, X_train, X_test, Y_train, Y_test)
    
def fit_xgb3(X_train, X_test, Y_train, Y_test):
    xgb = XGBClassifier(max_depth=3, n_estimators=1000)
    xgb.fit(X_train, Y_train)
    evaluate_model(xgb, X_train, X_test, Y_train, Y_test)
    
    
def fit_mlp(X_train, X_test, Y_train, Y_test):
    mlp = MLPClassifier(hidden_layer_sizes=(100, 100), activation='relu',
                        learning_rate_init=0.001, max_iter=100,
                        early_stopping=True, validation_fraction=0.2, n_iter_no_change=10)
    mlp.fit(X_train, Y_train)
    evaluate_model(mlp, X_train, X_test, Y_train, Y_test)
    return mlp

def run_experiment(X, Y, n_bootstraps=1):
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
    print("="*20 + "\nXGB-1\n" + "="*10)
    fit_xgb1(X_train.values, X_test.values, Y_train, Y_test)
    print("="*20 + "\nXGB-2\n" + "="*10)
    fit_xgb2(X_train.values, X_test.values, Y_train, Y_test)
    print("="*20 + "\nXGB-3\n" + "="*10)
    fit_xgb3(X_train.values, X_test.values, Y_train, Y_test)
    print("="*20 + "\nMLP\n" + "="*10)
    fit_mlp(X_train.values, X_test.values, Y_train, Y_test)
    print("="*20 + "\nEBM\n" + "="*10)
    ebm = ebc(outer_bags=10, interactions=0, max_bins=256, inner_bags=10)
    ebm.fit(X_train, Y_train)
    evaluate_model(ebm, X_train, X_test, Y_train, Y_test)
    print("="*20 + "\nCalibrated EBM\n" + "="*10)
    calibrated_ebm = CalibratedClassifierCV(base_estimator=ebm, cv=3)
    calibrated_ebm.fit(X, Y)
    evaluate_model(calibrated_ebm, X_train, X_test, Y_train, Y_test)
    ebm.fit(X, Y)
    ebm_global = ebm.explain_global()
    return ebm, ebm_global
