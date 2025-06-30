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
      return Response({ "error": "請傳入四筆路口特徵資料的清單"}, status = status.HTTP_400_BAD_REQUEST)

    # 使用預測器取得秒數
    preds = predictor.predict_batch(input_data)  # e.g. array([秒數1, 秒數2, 秒數3, 秒數4])

    # 東西向是第 0 與 1 筆，南北向是第 2 與 3 筆
    east_west_max = max(preds[0], preds[1])
    south_north_max = max(preds[2], preds[3])
    print(f"東西向最大秒數: {east_west_max}")
    print(f"南北向最大秒數: {south_north_max}")

    return Response({
        "east_west_seconds": int(east_west_max),
        "south_north_seconds": int(south_north_max),
    }, status = status.HTTP_200_OK)
