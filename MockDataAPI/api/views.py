from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
import pandas as pd
from django.http import JsonResponse
from datetime import datetime, timedelta
import json

@api_view(['GET'])
def mockData(request):
    if request.method == 'GET':
        csv_location = "../Dataset/XRPUSDT/XRPUSDT_5min.csv"
        df = pd.read_csv(csv_location)
        # df['timestamp'] = pd.to_datetime(df['timestamp'])

        if df.empty:
           return JsonResponse({"error": "CSV is empty"}, status=400)

        row_timestamp = datetime.strptime(request.GET.get('timestamp'), '%Y-%m-%d %H:%M:%S') + timedelta(minutes=5)
        latest_data = df.loc[df['timestamp'] == datetime.strftime(row_timestamp, '%Y-%m-%d %H:%M:%S')]

        return_data = {
            "timestamp": latest_data["timestamp"].item(),
            "open": latest_data["open"].item(),
            "high": latest_data["high"].item(),
            "low": latest_data["low"].item(),
            "close": latest_data["close"].item(),
            "volume": latest_data["volume"].item()
        }

        return Response(return_data, status=status.HTTP_200_OK)
    
@api_view(['POST'])
def mockTradeExecution(request):
    if request.method == "POST":
        trade_amount = float(request.data.get("trade_amount"))
        entry_price = float(request.data.get("entry_price"))
        shares = trade_amount / entry_price

        return Response({
            "shares": round(shares, 6),
            "entry_price": round(entry_price, 6)
        }, status=status.HTTP_200_OK)
    
@api_view(['GET'])
def mockTradeInfo(request):
    if request.method == "GET":
        signal = request.GET.get("signal")
        trade_amount = float(request.GET.get("trade_amount"))
        entry_price = float(request.GET.get("entry_price"))
        current_price = float(request.GET.get("current_price"))
        shares = trade_amount / entry_price

        if signal == "buy":
            trade_profit = (current_price - entry_price) * shares 
        elif signal == "sell":
            trade_profit = (entry_price - current_price) * shares
        else:
            return Response({
                "shares": 0,
                "profit": 0,
                "profit_percentage": 0
            }, status=status.HTTP_200_OK) 


        profit_percentage = (trade_profit / trade_amount) * 100

        return Response({
            "shares": round(shares, 6),
            "profit": round(trade_profit, 2),
            "profit_percentage": round(profit_percentage, 2)
        }, status=status.HTTP_200_OK)        

