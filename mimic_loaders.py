import pandas as pd
import numpy as np

from experiment_utils import clip_outliers, fillna_unknown_dtype_col

data_dir = "."

def parse_temp_range(x):
    parts = x.split("-")
    return (float(parts[0].split("[")[1]) + float(parts[1].split(")")[0])) / 2

# Load MIMIC-II
def load_mimic2():
    df = pd.read_csv(f"{data_dir}/mimic2/mimic2_rfimputed.csv")
    Y = df['HospitalMortality']
    X = df.copy()
    X = X.drop("HospitalMortality", axis=1)
    X['Temperature'] = [parse_temp_range(x) for x in X["Temperature"]]
    return X, Y


# Load MIMIC-III as tabular dataset.
def load_mimic3():
    df = pd.read_csv(f"{data_dir}/mimic3/adult_icu")
    X = df
    y = df['mort_icu'].values

    remove_cols = ['train', 'mort_icu', 'icustay_id', 'hadm_id', 'subject_id', 'adult_icu', 'admType_NEWBORN',
                   'sysbp_mean', 'sysbp_min', 'admType_ELECTIVE', 'admType_EMERGENCY', 'admType_URGENT', 
                   'heartrate_min', 'heartrate_mean',
                  'tempc_min', 'tempc_mean', 
                   'spo2_min', 'spo2_mean', 'spo2_max',
                   'glucose_min', 'glucose_max', 'first_hosp_stay', 'first_icu_stay',
                  'eth_asian', 'eth_other', 'eth_white', 'eth_black', 'eth_hispanic',
                  'resprate_min', 'resprate_mean', 'resprate_max',
                   'diasbp_max', 'diasbp_mean',
                  'meanbp_min', 'meanbp_mean', 'meanbp_max',
                  'hematocrit', 'bilirubin', 'hemoglobin']
    feature_names = list([x for x in df.columns.values if x not in remove_cols ])
    for col in remove_cols:
        del X[col]
    return X, y


def to_celcius(x):
    if x < 0:
        return x
    return (x-32)*(5./9)


# Load MIMIC-IV as tabular dataset.
def load_mimic4():
    df = pd.read_csv(f"{data_dir}/mimic4/mimic4_flat_large.csv", low_memory=False)
    df_cols = df.columns.tolist()
    # Match lab values to the ones used in the previous 2 MIMIC datasets.
    lab_cols = [
        'ART BP Diastolic',
        'ART BP Systolic',
        'Aortic Pressure Signal - Diastolic',
        'Aortic Pressure Signal - Systolic',
        'Arterial Blood Pressure diastolic',
        'Arterial Blood Pressure systolic',
        'Albumin',
        'Direct Bilirubin',
        'BUN',
        'Calcium Chloride',
        'Chloride (serum)',
        'Creatinine (serum)',
        'Cerebral Temperature (C)',
        'Glucose (serum)',
        'Hematocrit (serum)',
        'Hemoglobin',
        'Magnesium',
        'PTT',
        'Platelet Count',
        'Potassium (serum)',
        'Sodium (serum)',
        'Temperature Fahrenheit',
        'Temperature Site',
        'Skin Temperature',
        'RLE Temp',
        'RUE Temp',
        'Total Bilirubin',
        'WBC',]
    df.drop('Communication', axis=1, inplace=True)
    demo_cols = ['admission_type', 'insurance', 'marital_status', 'ethnicity', 'gender', 'age']
    treatment_cols = df_cols[df_cols.index('mortality')+1:df_cols.index('Insulin - Novolog')+1]
    treatment_cols = [x for x in treatment_cols if x != 'Communication']
    treatment_cols = np.array(treatment_cols)[np.sum(df[treatment_cols], axis=0) > 100]

    X_demo = df[demo_cols]
    X_treatments = df[treatment_cols]
    X_labs = clip_outliers(df[lab_cols])
    fill_values = {}
    for i in range(X_demo.shape[1]):
        if X_demo.values[0, i].__class__ == str:
            fill_values[i] = 'Missing'
        elif X_demo.values[0, i].__class__ == bool:
            fill_values[i] = False
        elif X_demo.values[0, i].__class__ == float or X_demo.values[0, i].__class__ == int:
            fill_values[i] = -1
    for j in range(X_labs.shape[1]):
        if X_labs.values[0, j].__class__ == str:
            fill_values[i+j] = 'Missing'
        elif X_labs.values[0, j].__class__ == bool:
            fill_values[i+j] = False
        elif X_labs.values[0, j].__class__ == float or X_labs.values[0, j].__class__ == int:
            fill_values[i+j] = -1
    X = pd.concat([X_demo, X_labs], axis=1).fillna(value=fill_values)
    Y = df['mortality']
    for feat in X.columns:
        X[feat] = fillna_unknown_dtype_col(X[feat])

    X["Temperature Fahrenheit"] = [to_celcius(x) for x in X["Temperature Fahrenheit"]]
    
    return X, Y, X_treatments
