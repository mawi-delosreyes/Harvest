from django.urls import path
from .views import mockData

urlpatterns = [
    path('getMockData/', mockData, name='mockData'),
]