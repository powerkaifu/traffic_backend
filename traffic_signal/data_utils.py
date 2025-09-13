"""
交通資料處理工具類別
"""
from django.db import transaction
from .models import Group, Intersection
from typing import List, Dict, Any, Optional
import uuid


class TrafficDataManager:
    """交通資料管理器"""

    @staticmethod
    def create_traffic_batch(
        traffic_data: List[Dict[str, Any]],
        east_west_seconds: Optional[int] = None,
        south_north_seconds: Optional[int] = None
    ) -> Group:
        """
        創建一批交通資料

        Args:
            traffic_data: 包含四個路口資料的列表
            east_west_seconds: 東西向最大綠燈秒數
            south_north_seconds: 南北向最大綠燈秒數

        Returns:
            Group: 創建的群組物件

        Raises:
            ValueError: 當資料格式不正確時
        """
        if not isinstance(traffic_data, list) or len(traffic_data) != 4:
            raise ValueError("必須提供四筆路口資料")

        # 驗證必要欄位
        required_fields = [
            'VD_ID', 'DayOfWeek', 'Hour', 'Minute', 'Second',
            'IsPeakHour', 'LaneID', 'LaneType', 'Speed', 'Occupancy',
            'Volume_M', 'Speed_M', 'Volume_S', 'Speed_S',
            'Volume_L', 'Speed_L'
        ]

        for i, data in enumerate(traffic_data):
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"第 {i+1} 筆資料缺少必要欄位: {field}")

        with transaction.atomic():
            # 創建 Group
            group = Group.objects.create(
                east_west_seconds=east_west_seconds,
                south_north_seconds=south_north_seconds
            )

            # 創建 Intersection 記錄
            for data in traffic_data:
                Intersection.objects.create(
                    group=group,
                    VD_ID=data['VD_ID'],
                    DayOfWeek=data['DayOfWeek'],
                    Hour=data['Hour'],
                    Minute=data['Minute'],
                    Second=data['Second'],
                    IsPeakHour=bool(data['IsPeakHour']),
                    LaneID=data['LaneID'],
                    LaneType=data['LaneType'],
                    Speed=data['Speed'],
                    Occupancy=data['Occupancy'],
                    Volume_M=data['Volume_M'],
                    Speed_M=data['Speed_M'],
                    Volume_S=data['Volume_S'],
                    Speed_S=data['Speed_S'],
                    Volume_L=data['Volume_L'],
                    Speed_L=data['Speed_L'],
                    Volume_T=data.get('Volume_T', 0),
                    Speed_T=data.get('Speed_T', 0.0),
                )

            return group

    @staticmethod
    def get_traffic_batch(group_id: str) -> Optional[Dict[str, Any]]:
        """
        取得特定批次的交通資料

        Args:
            group_id: 批次識別碼

        Returns:
            包含批次資料和路口明細的字典，如果找不到則返回 None
        """
        try:
            group = Group.objects.get(group_id=group_id)
            intersections = group.intersections.all()

            return {
                'group': {
                    'group_id': str(group.group_id),
                    'timestamp': group.timestamp,
                    'east_west_seconds': group.east_west_seconds,
                    'south_north_seconds': group.south_north_seconds,
                },
                'intersections': [
                    TrafficDataManager._intersection_to_dict(intersection)
                    for intersection in intersections
                ]
            }
        except Group.DoesNotExist:
            return None

    @staticmethod
    def get_recent_batches(limit: int = 10) -> List[Dict[str, Any]]:
        """
        取得最近的交通資料批次

        Args:
            limit: 限制返回的數量

        Returns:
            包含批次摘要資訊的列表
        """
        groups = Group.objects.all()[:limit]

        return [
            {
                'group_id': str(group.group_id),
                'timestamp': group.timestamp,
                'east_west_seconds': group.east_west_seconds,
                'south_north_seconds': group.south_north_seconds,
                'intersection_count': group.intersections.count(),
            }
            for group in groups
        ]

    @staticmethod
    def _intersection_to_dict(intersection: Intersection) -> Dict[str, Any]:
        """將 Intersection 物件轉換為字典"""
        return {
            'id': intersection.id,
            'VD_ID': intersection.VD_ID,
            'direction': intersection.get_direction_display,
            'DayOfWeek': intersection.DayOfWeek,
            'Hour': intersection.Hour,
            'Minute': intersection.Minute,
            'Second': intersection.Second,
            'IsPeakHour': intersection.IsPeakHour,
            'LaneID': intersection.LaneID,
            'LaneType': intersection.LaneType,
            'Speed': intersection.Speed,
            'Occupancy': intersection.Occupancy,
            'Volume_M': intersection.Volume_M,
            'Speed_M': intersection.Speed_M,
            'Volume_S': intersection.Volume_S,
            'Speed_S': intersection.Speed_S,
            'Volume_L': intersection.Volume_L,
            'Speed_L': intersection.Speed_L,
            'Volume_T': intersection.Volume_T,
            'Speed_T': intersection.Speed_T,
            'total_volume': intersection.total_volume,
            'created_at': intersection.created_at,
        }

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """取得資料庫統計資訊"""
        total_groups = Group.objects.count()
        total_intersections = Intersection.objects.count()

        # 取得最新一筆資料的時間
        latest_group = Group.objects.first()
        latest_timestamp = latest_group.timestamp if latest_group else None

        # 統計各方向的資料數量
        direction_stats = {}
        for choice_value, choice_label in Intersection.VD_ID_CHOICES:
            count = Intersection.objects.filter(VD_ID=choice_value).count()
            direction_stats[choice_label] = count

        return {
            'total_batches': total_groups,
            'total_intersections': total_intersections,
            'latest_timestamp': latest_timestamp,
            'direction_statistics': direction_stats,
        }


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
