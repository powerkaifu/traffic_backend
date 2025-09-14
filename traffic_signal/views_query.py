from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
import re
from .models import Group, Intersection


class TrafficQueryView(APIView):
    """統一的交通資料查詢 API - 支援日期範圍搜尋，同時取出 Group + Intersection 資料"""

    def get(self, request):
        """
        交通資料查詢 API - 僅支援日期範圍查詢

        查詢參數：
        - start_date: 開始日期 (YYYY-MM-DD) [必須]
        - end_date: 結束日期 (YYYY-MM-DD) [必須]

        使用範例：
        GET /api/traffic/query/?start_date=2024-01-01&end_date=2024-01-31

        回傳格式：
        {
          "query_info": {
            "period": "2024-01-01 ~ 2024-01-31",
            "data_points": 168
          },
          "data": [
            {
              "group": {
                "group_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2024-01-01T08:30:00Z",
                "east_west_seconds": 65,
                "south_north_seconds": 58
              },
              "intersections": [
                {
                  "id": 1,
                  "VD_ID": "VLRJX20",
                  "DayOfWeek": 1,
                  "Hour": 8,
                  "Minute": 30,
                  "Second": 0,
                  "IsPeakHour": true,
                  "LaneID": 0,
                  "LaneType": 1,
                  "Speed": 42.5,
                  "Occupancy": 15.3,
                  "Volume_M": 100,
                  "Speed_M": 45.2,
                  "Volume_S": 80,
                  "Speed_S": 48.1,
                  "Volume_L": 20,
                  "Speed_L": 35.8,
                  "Volume_T": 5,
                  "Speed_T": 30.0,
                  "total_volume": 205,
                  "created_at": "2024-01-01T08:30:00Z"
                }
              ]
            }
          ]
        }
        """
        try:
            # 取得查詢參數
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')

            # 驗證必要參數
            if not start_date_str or not end_date_str:
                return Response({
                    "error": "必須提供 start_date 和 end_date 參數 (格式: YYYY-MM-DD)"
                }, status=status.HTTP_400_BAD_REQUEST)

            # 日期格式驗證 YYYY-MM-DD
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'

            if not re.match(date_pattern, start_date_str):
                return Response({
                    "error": "start_date 格式錯誤，請使用 YYYY-MM-DD 格式"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not re.match(date_pattern, end_date_str):
                return Response({
                    "error": "end_date 格式錯誤，請使用 YYYY-MM-DD 格式"
                }, status=status.HTTP_400_BAD_REQUEST)

            # 解析日期
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            # end_date 設定為當天的 23:59:59
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

            # 驗證日期邏輯
            if start_date > end_date:
                return Response({
                    "error": "start_date 不能晚於 end_date"
                }, status=status.HTTP_400_BAD_REQUEST)

            # 查詢資料，包含關聯的 intersections
            groups = Group.objects.filter(
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).prefetch_related('intersections').order_by('timestamp')

            # 建立資料結構
            data = []
            for group in groups:
                intersections = group.intersections.all()
                data.append({
                    "group": {
                        "group_id": str(group.group_id),
                        "timestamp": group.timestamp.isoformat(),
                        "east_west_seconds": group.east_west_seconds,
                        "south_north_seconds": group.south_north_seconds,
                    },
                    "intersections": [{
                        "id": intersection.id,
                        "VD_ID": intersection.VD_ID,
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
                        "created_at": intersection.created_at.isoformat(),
                    } for intersection in intersections]
                })

            return Response({
                "query_info": {
                    "period": f"{start_date_str} ~ {end_date_str}",
                    "data_points": len(data)
                },
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": f"查詢失敗: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)