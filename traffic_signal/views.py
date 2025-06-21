from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class TrafficPrediction(APIView):

  def post(self, request):
    """
        預期接收前端送來四組路口特徵資料 (list of dict)
        範例 request.data:
        [
            {"Speed": ..., "Occupancy": ..., "Volume_M": ..., ...},
            {...}, {...}, {...}
        ]

        先回傳一個測試用的固定格式，之後你給我預測邏輯我幫你接入
        """
    input_data = request.data

    # 簡單檢查是否為 list 且長度是4
    if not isinstance(input_data, list) or len(input_data) != 4:
      return Response({ "error": "請送出四組路口特徵資料的列表"}, status = status.HTTP_400_BAD_REQUEST)

    # TODO: 之後實作預測邏輯
    # 目前回傳固定結果，每組路口回傳一個模擬綠燈秒數
    dummy_results = []
    for i in range(4):
      dummy_results.append({
          "intersection_id": i + 1,
          "predicted_green_seconds": 45  # 固定回傳 45 秒，待後續替換
      })

    return Response({ "predictions": dummy_results}, status = status.HTTP_200_OK)
