"""
交通資料處理工具類別
"""
from django.db import transaction
from .models import Group, Intersection
from typing import List, Dict, Any, Optional


class TrafficDataValidator:
    """交通資料驗證器"""

    @staticmethod
    def validate_intersection_data(data: Dict[str, Any]) -> List[str]:
        """
        驗證單筆路口資料

        Args:
            data: 路口資料字典

        Returns:
            錯誤訊息列表，如果沒有錯誤則為空列表
        """
        errors = []

        # 檢查必要欄位
        required_fields = [
            'VD_ID', 'DayOfWeek', 'Hour', 'Minute', 'Second',
            'IsPeakHour', 'LaneID', 'LaneType', 'Speed', 'Occupancy',
            'Volume_M', 'Speed_M', 'Volume_S', 'Speed_S',
            'Volume_L', 'Speed_L'
        ]

        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必要欄位: {field}")

        # 檢查 VD_ID 是否有效
        valid_vd_ids = [choice[0] for choice in Intersection.VD_ID_CHOICES]
        if data.get('VD_ID') not in valid_vd_ids:
            errors.append(f"無效的 VD_ID: {data.get('VD_ID')}")

        # 檢查時間範圍
        if not (1 <= data.get('DayOfWeek', 0) <= 7):
            errors.append("DayOfWeek 必須在 1-7 之間")

        if not (0 <= data.get('Hour', -1) <= 23):
            errors.append("Hour 必須在 0-23 之間")

        if not (0 <= data.get('Minute', -1) <= 59):
            errors.append("Minute 必須在 0-59 之間")

        if not (0 <= data.get('Second', -1) <= 59):
            errors.append("Second 必須在 0-59 之間")

        # 檢查數值範圍
        if data.get('Speed', -1) < 0:
            errors.append("Speed 不能為負數")

        if not (0 <= data.get('Occupancy', -1) <= 100):
            errors.append("Occupancy 必須在 0-100 之間")

        # 檢查流量數據
        volume_fields = ['Volume_M', 'Volume_S', 'Volume_L', 'Volume_T']
        for field in volume_fields:
            if data.get(field, 0) < 0:
                errors.append(f"{field} 不能為負數")

        return errors

    @staticmethod
    def validate_batch_data(traffic_data: List[Dict[str, Any]]) -> List[str]:
        """
        驗證整批交通資料

        Args:
            traffic_data: 包含四個路口資料的列表

        Returns:
            錯誤訊息列表
        """
        errors = []

        if not isinstance(traffic_data, list):
            errors.append("資料必須是列表格式")
            return errors

        if len(traffic_data) != 4:
            errors.append(f"必須包含四筆路口資料，目前有 {len(traffic_data)} 筆")
            return errors

        for i, data in enumerate(traffic_data):
            data_errors = TrafficDataValidator.validate_intersection_data(data)
            for error in data_errors:
                errors.append(f"第 {i+1} 筆資料: {error}")

        return errors
