from django.urls import path
from . import views

urlpatterns = [
    # 原有的API端點
    path('predict/', views.TrafficPrediction.as_view(), name='traffic_prediction'),
    path('data/', views.TrafficDataView.as_view(), name='traffic_data'),

    # 新增視覺化API端點
    path('analytics/', views.TrafficAnalyticsView.as_view(), name='traffic_analytics'),
    path('timeseries/', views.TrafficTimeSeriesView.as_view(), name='traffic_timeseries'),
]
