from django.urls import path
from .views import TrafficPrediction

urlpatterns = [
    path('predict/', TrafficPrediction.as_view(), name = 'traffic_predict'),
]
