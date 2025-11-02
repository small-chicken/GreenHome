from greenhome import settings
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,generics, permissions
from datetime import datetime, timezone, timedelta
import requests
import json
from django.contrib.auth.models import User

from .models import Appliance, EventInstance
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
        
# In your_app/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import CarbonPredictions  # <-- Your Model
from .scheduler_utils import scheduler # <-- Your Algorithm

class ScheduleTaskView(APIView):
    """
    API view to schedule a single task or a list of tasks.
    Receives task details via POST and returns the optimal start time(s).
    """
    permission_classes = [permissions.AllowAny] # Or AllowAny for testing

    def post(self, request, *args, **kwargs):
        
        # --- 1. GET DATA FROM THE *NESTED* JSON PAYLOAD ---
        
        # Get the list of appliances from the "appliances" key
        appliances_data = request.data.get('appliances')

        if not isinstance(appliances_data, list):
            return Response(
                {"error": "Invalid payload. Expected a JSON object with an 'appliances' list."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # This will hold the tasks in the format our scheduler function needs
        appliances_list = []
        
        try:
            # Loop through each appliance in the list (even if it's just one)
            for task in appliances_data:
                appliance_from_form = {
                    # FIX 1: Look for 'name', not 'appliance_type'
                    'name': task.get('name', 'user_task'), 
                    # FIX 2: Get data from the 'task' dictionary
                    'runtime_min': int(task.get('runtime_min')), 
                    'earliest_start': task.get('earliest_start'),
                    'latest_end': task.get('latest_end')
                }
                appliances_list.append(appliance_from_form)
            
        except (TypeError, ValueError, KeyError) as e:
            return Response(
                {"error": f"Invalid form data in appliance list: {e}. Check for missing fields or correct types."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Query the Database for the Latest Forecast (This part is correct)
        try:
            current_forecast_qs = CarbonPredictions.objects.order_by('timestamp')

            if not current_forecast_qs.exists():
                raise CarbonPredictions.DoesNotExist
                
            carbon_forecast_list = [f.carbon_intensity for f in current_forecast_qs]
            forecast_start_dt = current_forecast_qs.first().timestamp

        except CarbonPredictions.DoesNotExist:
            return Response(
                {"error": "Carbon forecast is not available. Please try again in a few minutes."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            return Response(
                {"error": f"Error loading forecast data: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 4. Run the Scheduler (This part is correct)
        schedule_result = scheduler(
            appliances_list, 
            carbon_forecast_list, 
            forecast_start_dt
        )

        # 5. Return the Optimal Time(s)
        return Response(schedule_result, status=status.HTTP_200_OK)