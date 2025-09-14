from django.urls import path
from . import views_save, views_query

urlpatterns = [
    # 儲存資料 API
    path('predict/', views_save.TrafficPrediction.as_view(), name='traffic_prediction'),

    # 統一查詢資料 API - 支援日期範圍搜尋，同時取出 Group + Intersection 資料
    path('query/', views_query.TrafficQueryView.as_view(), name='traffic_query'),
]
