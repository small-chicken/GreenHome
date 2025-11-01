from django.urls import path
from . import views

urlpatterns = [
    path('schedule/', views.ScheduleView.as_view(), name='schedule'),
    path('carbon-intensity/', views.CarbonIntensityView.as_view(), name='carbon_intensity'),
]
