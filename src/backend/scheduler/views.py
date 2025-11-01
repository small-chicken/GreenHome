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
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']    
        password = serializer.validated_data['password']
        user = authenticate(request, username=username, password=password)

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
    permission_classes = [permissions.IsAuthenticated]
    
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

class EnergyLoadView(APIView):
    # A view to get the single most recent 30-minute National Grid load.
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Fetches ONLY the single most recent 30-minute grid load data point.
        
        base_url = "https://api.bmreports.com/BMRS/datasets/ATL/stream"
        
        # Get current time and 60 minutes ago in UTC
        now_utc = datetime.now(timezone.utc)
        one_hour_ago_utc = now_utc - timedelta(hours=1)
        
        # Format datetimes for the API
        to_time_str = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        from_time_str = one_hour_ago_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

        params = {
            'APIKey': settings.ELEXON_API_KEY,
            'publishDateTimeFrom': from_time_str,
            'publishDateTimeTo': to_time_str,
            'format': 'json'
        }
        
        try:
            api_response = requests.get(base_url, params=params, timeout=20)
            api_response.raise_for_status()  # Check for HTTP errors
            
            data = api_response.json()
            
            # Check if data was returned and get the last item
            if data and isinstance(data, list) and len(data) > 0:
                
                # The API gives a list. We take the last one (-1).
                latest_record = data[-1]
                
                # Wrap the dictionary in a Response object
                return Response(latest_record, status=status.HTTP_200_OK)
                
            else:
                # Return a 404 Not Found response
                return Response(
                    {"message": "No data found in the specified time window."},
                    status=status.HTTP_404_NOT_FOUND
                )

        except requests.exceptions.HTTPError as err:
            print(f"HTTP error: {err}")
            if api_response.status_code == 403:
                print("HTTP 403 (Forbidden): Check that your API key is correct and active.")
                
            # Return a 502 Bad Gateway (the external API failed)
            return Response(
                {"error": "Failed to fetch data from external API."},
                status=status.HTTP_502_BAD_GATEWAY
            )
            
        except requests.exceptions.RequestException as err:
            print(f"An error occurred: {err}")
            
            # Return a 500 Internal Server Error
            return Response(
                {"error": "A server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )