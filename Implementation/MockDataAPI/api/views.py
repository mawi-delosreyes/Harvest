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
        csv_location = "../../Dataset/XRPUSDT/XRPUSDT_5min.csv"
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





