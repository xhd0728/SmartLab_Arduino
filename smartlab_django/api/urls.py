from django.urls import path
from . import views

urlpatterns = [
    path("test", views.APITestView.as_view()),
    path("set", views.OptionSetView.as_view()),
]
