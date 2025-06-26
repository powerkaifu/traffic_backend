import os
import json
import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model  # type: ignore

class Predictor:

  def __init__(self):
    # 模型和 scaler 路徑
    self.model_path = os.path.join(os.path.dirname(__file__), 'trained_model.keras')
    self.scaler_path = os.path.join(os.path.dirname(__file__), 'scaler.pkl')

    # 載入模型與 scaler
    if os.path.exists(self.model_path):
      self.model = load_model(self.model_path)
    else:
      self.model = None
      print("模型檔案不存在！")

    if os.path.exists(self.scaler_path):
      self.scaler = joblib.load(self.scaler_path)
    else:
      self.scaler = None
      print("Scaler 檔案不存在！")

    # 特徵欄位順序（與訓練時一致）
    self.feature_names = [
        'Speed',
        'Occupancy',
        'Volume_M',
        'Volume_S',
        'Volume_L',
        'Volume_T',
        'Speed_M',
        'Speed_S',
        'Speed_L',
        'Speed_T',
        'LaneID',
        'LaneType',
        'Hour',
        'DayOfWeek',
        'Minute',
        'Second',
        'IsPeakHour',
        'VD_ID_VLRJM60',
        'VD_ID_VLRJX00',
        'VD_ID_VLRJX20',
        'Occ_x_Volume_S',
        'Occ_x_Volume_L',
        'Occ_x_Volume_T',
        'SpeedS_x_VolumeS',
        'SpeedL_x_VolumeL',
        'SpeedT_x_VolumeT'
    ]

  def preprocess_and_scale(self, new_data_df: pd.DataFrame):
    # One-hot 編碼 VD_ID
    one_hot_vd_cols = [ col for col in self.feature_names if col.startswith('VD_ID_') ]
    new_data_df_processed = pd.get_dummies(new_data_df, columns = ['VD_ID'], prefix = 'VD_ID')

    # 補齊缺少的 one-hot 欄位
    for col in one_hot_vd_cols:
      if col not in new_data_df_processed.columns:
        new_data_df_processed[col] = 0

    # 數值型特徵
    numerical_features_to_scale = [
        'Speed', 'Occupancy', 'Volume_M', 'Volume_S', 'Volume_L', 'Volume_T', 'Speed_M', 'Speed_S', 'Speed_L', 'Speed_T', 'DayOfWeek', 'Hour', 'Minute', 'Second', 'LaneID', 'LaneType', 'IsPeakHour'
    ]
    existing_numerical = [ f for f in numerical_features_to_scale if f in new_data_df_processed.columns ]
    new_data_df_processed[existing_numerical] = new_data_df_processed[existing_numerical].astype(float)

    # 標準化
    scaled_values = self.scaler.transform(new_data_df_processed[existing_numerical])
    scaled_df = pd.DataFrame(scaled_values, columns = existing_numerical, index = new_data_df_processed.index)
    new_data_df_processed.loc[:, existing_numerical] = scaled_df

    # 補齊欄位順序並填 0
    X_new_final = pd.DataFrame(0, index = new_data_df_processed.index, columns = self.feature_names)
    for col in self.feature_names:
      if col in new_data_df_processed.columns:
        X_new_final[col] = new_data_df_processed[col]

    return X_new_final.values.astype(float)

  def predict_with_clipping(self, X_new_data, min_val = 20.0, max_val = 99.0):
    predicted = self.model.predict(X_new_data)
    clipped = np.clip(predicted, min_val, max_val)
    final = np.round(clipped).astype(int)
    return final.flatten()

  def predict_batch(self, input_list):
    """
        input_list: list of dict, 每筆為一筆特徵資料
        回傳：np.array 形狀 (n,) 的整數綠燈秒數預測結果
        """
    df = pd.DataFrame(input_list)
    X_new = self.preprocess_and_scale(df)
    preds = self.predict_with_clipping(X_new)
    return preds
