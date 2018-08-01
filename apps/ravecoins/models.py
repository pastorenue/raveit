from django.db import models

# Create your models here.
class Wallet(models.Model):
    member = models.ForeignKey(User)
    last_balance = models.DecimalField(max_digits=10, decimal_places=2)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    