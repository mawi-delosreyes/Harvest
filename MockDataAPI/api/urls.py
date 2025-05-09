from django.urls import path
from .views import mockData, mockTradeExecution, mockTradeInfo

urlpatterns = [
    path('getMockData/', mockData, name='mockData'),
    path('postMockTradeExecution/', mockTradeExecution, name='postMockTradeExecution'),
    path('getMockTradeInfo/', mockTradeInfo, name='getMockTradeInfo'),
]