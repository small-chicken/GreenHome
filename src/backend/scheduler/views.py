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
    # Response: JSON containing current carbon intensity and index.
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
        
# In your_app/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import CarbonPredictions  # <-- Your Model
from .scheduler_utils import scheduler # <-- Your Algorithm

def T(days=0, hours=0, minutes=0):
    dt = FORECAST_START + timedelta(days=days, hours=hours, minutes=minutes)
    return dt.isoformat()


class ScheduleEventsView(APIView):
    permission_classes = [permissions.AllowAny] 

    def post(self, request, *args, **kwargs):
        appliances_data = request.data.get('appliances')
        if not isinstance(appliances_data, list) or not appliances_data:
            return Response(
                {"error": "Expected a list of appliances."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Load your forecast data (same as before)
        from .models import CarbonPredictions, Appliance, EventInstance
        from .scheduler_utils import scheduler
        from datetime import datetime, timedelta, timezone

        try:
            forecast_qs = CarbonPredictions.objects.order_by("timestamp")
            if not forecast_qs.exists():
                return Response({"error": "No carbon forecast available."}, status=503)
            forecast_start = forecast_qs.first().timestamp
            carbon_forecast = [f.carbon_intensity for f in forecast_qs]
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        # Prepare appliances list
        formatted = []
        for a in appliances_data:
            formatted.append({
                "name": a.get("name", "Unnamed task"),
                "runtime_min": int(a.get("runtime_min", 0)),
                "earliest_start": a.get("earliest_start"),
                "latest_end": a.get("latest_end"),
            })

        # Run scheduler
        result = scheduler(formatted, carbon_forecast, forecast_start)

        # Save results
        created = []
        for app in formatted:
            start_iso = result.get(app["name"])
            if not start_iso:
                continue
            start_time = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            end_time = start_time + timedelta(minutes=app["runtime_min"])

            appliance_obj, _ = Appliance.objects.get_or_create(name=app["name"])
            evt = EventInstance.objects.create(
                appliance=appliance_obj,
                start_time=start_time,
                end_time=end_time,
            )
            created.append(evt)

        from .serializers import EventInstanceSerializer
        serializer = EventInstanceSerializer(created, many=True)
        return Response(serializer.data, status=201)


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