import string
import random
from django.contrib.auth.models import User
from django.db import models
from django.db.models import permalink
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from datetime import datetime, timedelta
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class CreditOrder(models.Model):
    CANCELLED = 'Cancelled'
    REFUNDED = 'Refunded'
    CONFIRMED = 'Confirmed'
    FAILED = 'Failed'
    RENEGADE = 'Renegade'
    PROCESSING = 'Processing'
    
    ORDER_STATUS = (
        (CANCELLED, 'Cancelled'),
        (REFUNDED, 'Refunded'),
        (CONFIRMED, 'Confirmed'),
        (FAILED, 'Failed'),
        (RENEGADE, 'Renegade'),
        (PROCESSING, 'Processing'),
    )
    
    NAIRA = 'Naira'
    DOLLARS = 'Dollars'
    
    PAYMENT_CURRENCY = (
        (NAIRA, "Naira"),
        (DOLLARS, "Dollars"),
    )
    
    GTPAY = 'Bank'
    PAYPAL = 'PayPal'
    
    PAYMENT_METHOD = (
        (GTPAY, "GTPay"),
        (PAYPAL, 'PayPal'),
    )
    
    customer = models.ForeignKey('account.Customer', related_name='credit_orders')
    number_of_credit = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    currency = models.CharField(max_length=10, choices=PAYMENT_CURRENCY, default=DOLLARS)
    order_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=30, unique=True, db_index=True)
    transaction_status = models.CharField(max_length=30, choices=ORDER_STATUS)
    status_code = models.CharField(max_length=30, null=True, blank=True)
    status = models.CharField(max_length=200, null=True, blank=True)
    payment_method = models.CharField(editable=False, max_length=30, choices=PAYMENT_METHOD)
    last_card_digits = models.CharField(max_length=100, null=True, blank=True)
    paymentReference = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return "%s " % (self.transaction_id)

    @property
    def amount_in_kobo(self):
        return int(self.amount * 100)


class CreditUsage(models.Model):
    customer = models.ForeignKey('account.Customer', related_name='credit_usages')
    credit_before = models.IntegerField()
    credit_after = models.IntegerField()
    order = models.OneToOneField('order.Order')
    transaction_date = models.DateTimeField(auto_now_add=True)


class Order(models.Model):    
    member = models.ForeignKey('account.Member', related_name='orders')
    amount = models.DecimalField(editable=False, default=0, decimal_places=2, max_digits=8)
    quantity = models.IntegerField()
    transaction_id = models.CharField(max_length=30)
    created_on = models.DateTimeField(auto_now_add=True, verbose_name=_('Order date'))
    creation_date = models.DateField(auto_now_add=True, editable=False)
    order_status = models.CharField(max_length=13, choices=CreditOrder.ORDER_STATUS, null=True, blank=True)
    paystack_reference = models.CharField(max_length=25, blank=True, null=True)
    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return self.transaction_id
    
    @property
    def amount_in_kobo(self):
        return '%s' % int(self.amount * 100)

    def save(self, *args, **kwargs):
        self.creation_date = datetime.now().date()
        super(Order, self).save(*args, **kwargs)