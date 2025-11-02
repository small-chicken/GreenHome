from greenhome import settings
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from datetime import datetime, timezone, timedelta
import requests
import json
from django.contrib.auth.models import User

from .models import Appliance, EventInstance
from .serializers import EventInstanceSerializer
from .scheduler_alg import scheduler

from .serializers import UserSerializer, RegisterSerializer, LoginSerializer
#  Login + Register Views

# Sign up with user, returns nothing, just create user
class RegisterView(generics.CreateAPIView):
    """
    View to attempt signup with username, email and password.

    Returns:
        Response: access and refresh JWT tokens along with user data upon successful registration. Error if not successful.
    """
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()


        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)



# Login with user credentials, returns JWT tokens
class LoginView(APIView):
    """
    View to attempt login with username and password.

    Returns:
        Response: JSON containing JWT tokens and user data if successful, error message otherwise.
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print("DEBUG FRONTEND DATA:", request.data)
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        #username = serializer.validated_data['username']    
        #user = authenticate(request, username=username, password=password)
        ##password = serializer.validated_data['password']

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            },status = status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)



class CarbonIntensityView(APIView):
    # View to fetch current carbon intensity data from the UK Carbon Intensity API.
    # Requires Authentication
    # Returns:
    #     Response: JSON containing current carbon intensity and index.
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        url = "https://api.carbonintensity.org.uk/intensity"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            intensity = data["data"][0]["intensity"]["actual"]
            index = data["data"][0]["intensity"]["index"]

            return Response({"intensity": intensity, "index": index}, status=200)

        except requests.RequestException as e:
            return Response({"error": "Failed to fetch carbon intensity data"}, status=500)


class HistoricCarbonIntensity(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        url = "https://api.carbonintensity.org.uk/intensity/2017-08-25T12:35Z/2017-15-25T12:35Z"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            

            return 
        except requests.RequestException as e:
            return Response({"error": "Failed to fetch carbon intensity data"}, status=500)
        
class ScheduleEventsView(APIView):
    permission_classes = [permissions.AllowAny]  # temporarily disabled auth

    def post(self, request):
        try:
            appliances = request.data.get("appliances", [])
            if not appliances:
                return Response({"error": "No appliances provided"}, status=status.HTTP_400_BAD_REQUEST)

            # --- Try to get 48-hour carbon intensity forecast from the API ---
            forecast_url = "https://api.carbonintensity.org.uk/intensity/fw48h"
            carbon_forecast = []
            forecast_start_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

            try:
                resp = requests.get(forecast_url, timeout=10)
                resp.raise_for_status()
                forecast_data = resp.json().get("data", [])

                if forecast_data:
                    carbon_forecast = [period["intensity"]["forecast"] for period in forecast_data]
                    forecast_start_time = datetime.fromisoformat(
                        forecast_data[0]["from"].replace("Z", "+00:00")
                    )
                    print(f"✅ Successfully fetched {len(carbon_forecast)} forecast slots.")
                else:
                    raise ValueError("Empty forecast data")

            except Exception as e:
                # --- Fallback dummy pattern if the API fails ---
                print(f"⚠️ Carbon API failed ({e}), using fallback forecast data instead.")

                peak_cost = 100
                mid_cost = 50
                low_cost = 20

                day_pattern = (
                    [low_cost] * 12 +       # 00:00 - 05:45 (Overnight low)
                    [peak_cost] * 6 +       # 06:00 - 08:45 (Morning peak)
                    [mid_cost] * 8 +        # 09:00 - 12:45 (Daytime)
                    [low_cost] * 8 +        # 13:00 - 16:45 (Solar peak / Midday low)
                    [peak_cost] * 10 +      # 17:00 - 21:45 (Evening peak)
                    [mid_cost] * 4          # 22:00 - 23:45 (Dropping off)
                )
                carbon_forecast = day_pattern * 2  # 48 hours = 96 half-hour slots
                forecast_start_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

            # --- Sanity check ---
            if len(carbon_forecast) != 96:
                return Response({"error": f"Invalid forecast length ({len(carbon_forecast)})"}, status=500)

            # --- Run the scheduler ---
            optimal_schedule = scheduler(appliances, carbon_forecast, forecast_start_time)

            saved_events = []
            for app in appliances:
                name = app["name"]
                best_start = optimal_schedule.get(name)
                if not best_start:
                    continue

                start_time = datetime.fromisoformat(best_start)
                end_time = start_time + timedelta(minutes=app["runtime_min"])

                saved_events.append({
                    "appliance": name,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                })

            return Response({
                "message": "✅ Events scheduled successfully",
                "schedule": saved_events
            }, status=200)

        except Exception as e:
            print("Scheduler error:", e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserEventsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self,request):
        username = request.query_params.get("username")

        if not username:
            return Response({"error": "Username not provided"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": f"User '{username}' not found"}, status=status.HTTP_404_NOT_FOUND)


        events = EventInstance.objects.filter(user_id=user).order_by("start_time")

        serializer = EventInstanceSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)