import os
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
        'SpeedT_x_VolumeT',
        'Flow_Speed_Index',
        'Volume_Weighted_Speed',
        'Congestion_Index',
        'Throughput_Potential',
        'Flow_Speed_Balance'
    ]

  def preprocess_and_scale(self, new_data_df: pd.DataFrame):
    one_hot_vd_cols = [ col for col in self.feature_names if col.startswith('VD_ID_') ]
    new_data_df_processed = pd.get_dummies(new_data_df, columns = ['VD_ID'], prefix = 'VD_ID')

    # 補齊缺少的 one-hot 欄位
    for col in one_hot_vd_cols:
      if col not in new_data_df_processed.columns:
        new_data_df_processed[col] = 0

    # ⭐️ 新增：計算 5 個複合特徵（A+B+D 方案）
    # 這些特徵在訓練時已經計算過，預測時也要計算
    total_volume = new_data_df_processed['Volume_S'] + new_data_df_processed['Volume_M'] + new_data_df_processed['Volume_L']

    new_data_df_processed['Flow_Speed_Index'] = (total_volume + 0.1) / (new_data_df_processed['Speed'] + 0.1)
    new_data_df_processed['Volume_Weighted_Speed'] = (
        new_data_df_processed['Volume_S'] * new_data_df_processed['Speed_S'] + new_data_df_processed['Volume_M'] * new_data_df_processed['Speed_M'] +
        new_data_df_processed['Volume_L'] * new_data_df_processed['Speed_L']
    ) / (total_volume + 0.1)
    new_data_df_processed['Congestion_Index'] = (new_data_df_processed['Occupancy'] * (total_volume + 1) * (50 - new_data_df_processed['Speed']).clip(lower = 0)) / 100
    new_data_df_processed['Throughput_Potential'] = new_data_df_processed['Volume_T'] * new_data_df_processed['Speed_T'] / (100 + 0.1)
    new_data_df_processed['Flow_Speed_Balance'] = (total_volume + 0.1) / (new_data_df_processed['Speed'] + 1)

    numerical_features_to_scale = [
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
        'DayOfWeek',
        'Hour',
        'Minute',
        'Second',
        'LaneID',
        'LaneType',
        'IsPeakHour',  # ⭐️ 新增複合特徵到標準化列表
        'Flow_Speed_Index',
        'Volume_Weighted_Speed',
        'Congestion_Index',
        'Throughput_Potential',
        'Flow_Speed_Balance',
    ]
    existing_numerical = [ f for f in numerical_features_to_scale if f in new_data_df_processed.columns ]
    new_data_df_processed[existing_numerical] = new_data_df_processed[existing_numerical].astype(float)

    # 標準化
    scaled_values = self.scaler.transform(new_data_df_processed[existing_numerical])
    scaled_df = pd.DataFrame(scaled_values, columns = existing_numerical, index = new_data_df_processed.index)
    new_data_df_processed.loc[:, existing_numerical] = scaled_df

    # ⭐️ 方案 A：特徵重縮放 - 強化 Volume 和 Speed 的權重，減弱時間特徵
    # 必須與訓練時相同，否則模型行為會不一致
    new_data_df_processed['Volume_S'] = new_data_df_processed['Volume_S'] * 2.5
    new_data_df_processed['Volume_M'] = new_data_df_processed['Volume_M'] * 2.5
    new_data_df_processed['Volume_L'] = new_data_df_processed['Volume_L'] * 2.5
    new_data_df_processed['Volume_T'] = new_data_df_processed['Volume_T'] * 2.5

    new_data_df_processed['Speed'] = new_data_df_processed['Speed'] * 3.0
    new_data_df_processed['Speed_S'] = new_data_df_processed['Speed_S'] * 2.5
    new_data_df_processed['Speed_M'] = new_data_df_processed['Speed_M'] * 2.5
    new_data_df_processed['Speed_L'] = new_data_df_processed['Speed_L'] * 2.5
    new_data_df_processed['Speed_T'] = new_data_df_processed['Speed_T'] * 2.5

    new_data_df_processed['IsPeakHour'] = new_data_df_processed['IsPeakHour'] * 0.6
    new_data_df_processed['Hour'] = new_data_df_processed['Hour'] * 0.8
    new_data_df_processed['DayOfWeek'] = new_data_df_processed['DayOfWeek'] * 0.9
    new_data_df_processed['Minute'] = new_data_df_processed['Minute'] * 0.7
    new_data_df_processed['Second'] = new_data_df_processed['Second'] * 0.7

    new_data_df_processed['Flow_Speed_Index'] = new_data_df_processed['Flow_Speed_Index'] * 2.0
    new_data_df_processed['Volume_Weighted_Speed'] = new_data_df_processed['Volume_Weighted_Speed'] * 1.5
    new_data_df_processed['Congestion_Index'] = new_data_df_processed['Congestion_Index'] * 2.0
    new_data_df_processed['Throughput_Potential'] = new_data_df_processed['Throughput_Potential'] * 1.5
    new_data_df_processed['Flow_Speed_Balance'] = new_data_df_processed['Flow_Speed_Balance'] * 2.0

    # 補齊欄位順序並填 0
    X_new_final = pd.DataFrame(0, index = new_data_df_processed.index, columns = self.feature_names)
    for col in self.feature_names:
      if col in new_data_df_processed.columns:
        X_new_final[col] = new_data_df_processed[col]

    return X_new_final.values.astype(float)

  def predict_with_clipping(self, X_new_data, min_val = 30.0, max_val = 99.0):
    """
      使用模型進行預測，並將結果裁剪到指定範圍內。
      """
    predicted_green_seconds_raw = self.model.predict(X_new_data)

    # 對每個預測值進行裁剪
    clipped_green_seconds = np.clip(predicted_green_seconds_raw, min_val, max_val)

    # 四捨五入並轉換為整數
    final_green_seconds = np.round(clipped_green_seconds).astype(int)

    return final_green_seconds

  def predict_batch(self, input_list):
    """
        input_list: list of dict, 每筆為一筆特徵資料
        回傳：np.array 形狀 (n,) 的整數綠燈秒數預測結果
        """
    df = pd.DataFrame(input_list)
    X_new = self.preprocess_and_scale(df)
    preds = self.predict_with_clipping(X_new)
    return preds
