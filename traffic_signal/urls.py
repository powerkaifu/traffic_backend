from django.urls import path
from .views import TrafficPrediction, TrafficDataView

urlpatterns = [
    path('predict/', TrafficPrediction.as_view(), name='traffic_predict'),
    path('data/', TrafficDataView.as_view(), name='traffic_data'),
]
