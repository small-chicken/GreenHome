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
    appliance = models.ForeignKey(Appliance, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    green_score = models.FloatField()
    status = models.CharField(max_length=50, default = "scheduled")  # e.g., scheduled, completed, cancelled

    def __str__(self):
        return f"Event for {self.appliance.name} by {self.user.username} at {self.start_time}"

    class Meta:
        verbose_name_plural = "Event Instances"

class GreenHourPrediction(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    predicted_start = models.DateTimeField()
    predicted_end = models.DateTimeField()
    renewable_percentage = models.FloatField()
    confidence = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Prediction {self.timestamp} ({self.renewable_percentage:.1f}%)"

    class Meta:
        verbose_name_plural = "Green Hour Predictions"

__all__ = ["scheduler"]