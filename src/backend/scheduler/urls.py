from django.urls import path
from . import views

urlpatterns = [
    path('carbon-intensity/', views.CarbonIntensityView.as_view(), name='carbon_intensity'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('historic-data/', views.HistoricCarbonIntensity.as_view(), name='historic-data'),
    path('schedule/', views.ScheduleEventsView.as_view(), name='schedule-events'),
    path("events/", views.UserEventsView.as_view(), name="user-events-by-name")
]
