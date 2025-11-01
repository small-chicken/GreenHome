from django.shortcuts import render
from django.views import View
from django.http import HttpResponse

from django.http import JsonResponse
from django.views import View
import requests

class CarbonIntensityView(View):
    def get(self, request):
        url = "https://api.carbonintensity.org.uk/intensity"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            intensity = data["data"]["intensity"]["actual"]
            index = data["data"]["intensity"]["index"]

            return JsonResponse({
                "intensity": intensity,
                "index": index
            })

        except requests.RequestException as e:
            return JsonResponse({"error": str(e)}, status=500)


class ScheduleView(View):
    def get(self, request):
        return HttpResponse("Initial schedule view ")