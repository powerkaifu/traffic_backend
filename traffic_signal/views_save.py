from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Group, Intersection
from .ml.predictor import Predictor

predictor = Predictor()  # 初始化一次


class TrafficPrediction(APIView):
    """
    交通號誌預測 API
    接收四個路口的交通資料，進行預測並儲存結果
    """

    def post(self, request):
        """
        範例：交通號誌預測 API
        POST /api/traffic/predict/
        Content-Type: application/json

        Body (JSON):
        [
          {
            "VD_ID": "VLRJX20",
            "DayOfWeek": 1,
            "Hour": 8,
            "Minute": 30,
            "Second": 0,
            "IsPeakHour": 1,
            "LaneID": 1,
            "LaneType": "直行",
            "Speed": 42.5,
            "Occupancy": 15.3,
            "Volume_M": 100,
            "Speed_M": 45.2,
            "Volume_S": 80,
            "Speed_S": 48.1,
            "Volume_L": 20,
            "Speed_L": 35.8,
            "Volume_T": 5,
            "Speed_T": 30.0
          },
          ...共4筆路口資料...
        ]

        回傳範例：
        {
          "group_id": "123e4567-e89b-12d3-a456-426614174000",
          "east_west_seconds": 65,
          "south_north_seconds": 58,
          "timestamp": "2024-01-01T08:30:00Z",
          "message": "資料已成功儲存並完成預測"
        }

        錯誤回傳：
        {
          "error": "請傳入四筆路口特徵資料的清單"
        }
        """
        input_data = request.data
        print(f"收到的輸入資料: {input_data}")

        # 確認輸入是 list 且有四筆資料
        if not isinstance(input_data, list) or len(input_data) != 4:
            return Response({
                "error": "請傳入四筆路口特徵資料的清單"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 使用預測器取得秒數
            preds = predictor.predict_batch(input_data)

            # 驗證預測結果
            if len(preds) != 4:
                return Response({
                    "error": "預測結果格式錯誤"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 東西向是第 0 與 1 筆，南北向是第 2 與 3 筆
            east_west_max = max(preds[0], preds[1])
            south_north_max = max(preds[2], preds[3])

            # 只限制最大秒數，移除最小秒數限制
            MAX_SECONDS = 99  # 最多99秒

            east_west_seconds = min(int(east_west_max), MAX_SECONDS)
            south_north_seconds = min(int(south_north_max), MAX_SECONDS)

            # 詳細打印預測結果
            print("\n" + "=" * 80)
            print("🟢 交通信號預測結果")
            print("=" * 80)
            print(f"路口 0 (東方向 VD_ID={input_data[0].get('VD_ID')}): {int(preds[0])} 秒")
            print(f"路口 1 (西方向 VD_ID={input_data[1].get('VD_ID')}): {int(preds[1])} 秒")
            print(f"路口 2 (南方向 VD_ID={input_data[2].get('VD_ID')}): {int(preds[2])} 秒")
            print(f"路口 3 (北方向 VD_ID={input_data[3].get('VD_ID')}): {int(preds[3])} 秒")
            print("-" * 80)
            print(f"📊 東西向最大綠燈秒數: {east_west_seconds} 秒 (最大({int(preds[0])}, {int(preds[1])}))")
            print(f"📊 南北向最大綠燈秒數: {south_north_seconds} 秒 (最大({int(preds[2])}, {int(preds[3])}))")
            print("=" * 80 + "\n")

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
            return Response({
                "error": f"預測處理失敗: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)