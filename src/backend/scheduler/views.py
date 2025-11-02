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