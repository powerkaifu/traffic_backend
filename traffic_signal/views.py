from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Group, Intersection
from .ml.predictor import Predictor
import uuid

predictor = Predictor()  # 初始化一次


class TrafficPrediction(APIView):

    def post(self, request):
        input_data = request.data
        print("收到的請求資料:", input_data)

        # 確認輸入是 list 且有四筆資料
        if not isinstance(input_data, list) or len(input_data) != 4:
            return Response({
                "error": "請傳入四筆路口特徵資料的清單"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 使用預測器取得秒數
            print("收到的輸入資料:", input_data)
            preds = predictor.predict_batch(input_data)  # e.g. array([東_秒數1, 西_秒數2, 南_秒數3, 北_秒數4])

            # 驗證預測結果
            if len(preds) != 4:
                return Response({
                    "error": "預測結果格式錯誤"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 東西向是第 0 與 1 筆，南北向是第 2 與 3 筆
            east_west_max = max(preds[0], preds[1])
            south_north_max = max(preds[2], preds[3])

            # 設定最小和最大秒數限制
            MIN_SECONDS = 40  # 最少40秒
            MAX_SECONDS = 120  # 最多120秒

            east_west_seconds = max(MIN_SECONDS, min(int(east_west_max), MAX_SECONDS))
            south_north_seconds = max(MIN_SECONDS, min(int(south_north_max), MAX_SECONDS))

            print(f"東西向最大秒數: {east_west_seconds}")
            print(f"南北向最大秒數: {south_north_seconds}")

            # 使用事務來確保資料一致性
            with transaction.atomic():
                # 1. 創建 Group 記錄
                group = Group.objects.create(
                    east_west_seconds=east_west_seconds,
                    south_north_seconds=south_north_seconds
                )

                # 2. 創建 Intersection 記錄
                for intersection_data in input_data:
                    Intersection.objects.create(
                        group=group,
                        VD_ID=intersection_data.get('VD_ID'),
                        DayOfWeek=intersection_data.get('DayOfWeek'),
                        Hour=intersection_data.get('Hour'),
                        Minute=intersection_data.get('Minute'),
                        Second=intersection_data.get('Second'),
                        IsPeakHour=bool(intersection_data.get('IsPeakHour', 0)),
                        LaneID=intersection_data.get('LaneID'),
                        LaneType=intersection_data.get('LaneType'),
                        Speed=intersection_data.get('Speed'),
                        Occupancy=intersection_data.get('Occupancy'),
                        Volume_M=intersection_data.get('Volume_M'),
                        Speed_M=intersection_data.get('Speed_M'),
                        Volume_S=intersection_data.get('Volume_S'),
                        Speed_S=intersection_data.get('Speed_S'),
                        Volume_L=intersection_data.get('Volume_L'),
                        Speed_L=intersection_data.get('Speed_L'),
                        Volume_T=intersection_data.get('Volume_T', 0),
                        Speed_T=intersection_data.get('Speed_T', 0.0),
                    )

            return Response({
                "group_id": str(group.group_id),
                "east_west_seconds": east_west_seconds,
                "south_north_seconds": south_north_seconds,
                "timestamp": group.timestamp.isoformat(),
                "message": "資料已成功儲存並完成預測"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"預測錯誤: {str(e)}")
            return Response({
                "error": f"預測處理失敗: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrafficDataView(APIView):
    """用於查詢交通資料的 API"""

    def get(self, request):
        """取得交通資料列表"""
        try:
            # 取得查詢參數
            group_id = request.query_params.get('group_id')
            limit = request.query_params.get('limit', 10)

            if group_id:
                # 查詢特定批次
                try:
                    group = Group.objects.get(group_id=group_id)
                    intersections = group.intersections.all()

                    return Response({
                        "group": {
                            "group_id": str(group.group_id),
                            "timestamp": group.timestamp.isoformat(),
                            "east_west_seconds": group.east_west_seconds,
                            "south_north_seconds": group.south_north_seconds,
                        },
                        "intersections": [{
                            "id": intersection.id,
                            "VD_ID": intersection.VD_ID,
                            "direction": intersection.get_direction_display,
                            "DayOfWeek": intersection.DayOfWeek,
                            "Hour": intersection.Hour,
                            "Minute": intersection.Minute,
                            "Second": intersection.Second,
                            "IsPeakHour": intersection.IsPeakHour,
                            "LaneID": intersection.LaneID,
                            "LaneType": intersection.LaneType,
                            "Speed": intersection.Speed,
                            "Occupancy": intersection.Occupancy,
                            "Volume_M": intersection.Volume_M,
                            "Speed_M": intersection.Speed_M,
                            "Volume_S": intersection.Volume_S,
                            "Speed_S": intersection.Speed_S,
                            "Volume_L": intersection.Volume_L,
                            "Speed_L": intersection.Speed_L,
                            "Volume_T": intersection.Volume_T,
                            "Speed_T": intersection.Speed_T,
                            "total_volume": intersection.total_volume,
                        } for intersection in intersections]
                    }, status=status.HTTP_200_OK)

                except Group.DoesNotExist:
                    return Response({
                        "error": "找不到指定的批次資料"
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # 查詢最近的資料
                groups = Group.objects.all()[:int(limit)]

                return Response({
                    "groups": [{
                        "group_id": str(group.group_id),
                        "timestamp": group.timestamp.isoformat(),
                        "east_west_seconds": group.east_west_seconds,
                        "south_north_seconds": group.south_north_seconds,
                        "intersection_count": group.intersections.count(),
                    } for group in groups]
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"查詢失敗: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
