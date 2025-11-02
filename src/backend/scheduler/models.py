from django.db import models
from django.contrib.auth.models import User

class Appliance(models.Model):
    name = models.CharField(max_length=200)
    average_power_Kwh = models.FloatField()
    average_duration = models.DurationField()
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Appliances"

class ApplianceProperty(models.Model):
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    frequency_per_week = models.IntegerField()
    earliest_start_time = models.TimeField()
    latest_end_time = models.TimeField()
    preferred_days = models.CharField(max_length=100)
    preferred_start_time = models.TimeField()


    def __str__(self):
        return f"{self.appliance.name} properties for {self.user.username}"

    class Meta:
        verbose_name_plural = "Appliance Properties"

class EventInstance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    appliance = models.CharField(max_length=100)
    start_time = models.DateTimeField()


    def __str__(self):
        return f"Event for {self.appliance.name} by {self.user.username} at {self.start_time}"

    class Meta:
        verbose_name_plural = "Event Instances"

class CarbonPredictions(models.Model):
    timestamp = models.DateTimeField()
    carbon_intensity = models.FloatField()  # e.g., grams of CO2 per kWh

    def __str__(self):
        return f"Carbon Intensity at {self.timestamp}: {self.carbon_intensity} gCO2/kWh"

    class Meta:
        verbose_name_plural = "Carbon Predictions"



__all__ = ["scheduler"]