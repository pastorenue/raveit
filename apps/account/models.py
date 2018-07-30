from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=50, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    key = models.CharField(max_length=255, null=True, db_index=True)
    verified = models.BooleanField(default=False)
    credit = models.IntegerField(default= 1)
    payment_authorized = models.BooleanField(default=False)
    payment_authorization_code = models.CharField(max_length=25, null=True, blank=True)

    def __unicode__(self):
        return "%s, %s" % (self.user.first_name, self.user.last_name)