from django.urls import path
from . import views

urlpatterns = [
    path("set", views.OptionSetView.as_view()),
    path("history", views.DeviceHistoryView.as_view()),
    path("echarts", views.EChartsView.as_view()),
]
