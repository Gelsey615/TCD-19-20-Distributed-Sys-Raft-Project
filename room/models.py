from django.db import models


class Room(models.Model):
    room_id = models.IntegerField(primary_key=True)
    room_type = models.CharField(max_length=200)
    room_floor = models.IntegerField()


class BookInfo(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    transaction_id = models.IntegerField(primary_key=True)
    checkin_time = models.DateTimeField()
    checkout_time = models.DateTimeField()
    customer_name = models.CharField(max_length=200)
    customer_email = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=200)
