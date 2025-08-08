from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .ml.predictor import Predictor

predictor = Predictor()  # 初始化一次


class TrafficPrediction(APIView):

    def post(self, request):
        input_data = request.data

        # 確認輸入是 list 且有四筆資料
        if not isinstance(input_data, list) or len(input_data) != 4:
            return Response({"error": "請傳入四筆路口特徵資料的清單"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 使用預測器取得秒數
            print("收到的輸入資料:", input_data)
            preds = predictor.predict_batch(input_data)  # e.g. array([東_秒數1, 西_秒數2, 南_秒數3, 北_秒數4])

            # 驗證預測結果
            if len(preds) != 4:
                return Response({"error": "預測結果格式錯誤"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 東西向是第 0 與 1 筆，南北向是第 2 與 3 筆
            east_west_max = max(preds[0], preds[1])
            south_north_max = max(preds[2], preds[3])

            # 設定最小和最大秒數限制
            MIN_SECONDS = 40  # 最少40秒
            MAX_SECONDS = 120  # 最多120秒

            east_west_seconds = max(MIN_SECONDS, min(int(east_west_max), MAX_SECONDS) )
            south_north_seconds = max(MIN_SECONDS, min(int(south_north_max), MAX_SECONDS) )

            print(f"東西向最大秒數: {east_west_seconds}")
            print(f"南北向最大秒數: {south_north_seconds}")

            return Response({
                "east_west_seconds": east_west_seconds,
                "south_north_seconds": south_north_seconds,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"預測錯誤: {str(e)}")
            return Response({"error": "預測處理失敗"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
