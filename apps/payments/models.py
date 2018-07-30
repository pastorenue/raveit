from django.db import models
from datetime import timedelta
from django.conf import settings
from config.utils import pin_generator
# Create your models here.

class AccessCard(models.Model):
    student = models.ForeignKey('students.Student', null=True)
    access_code = models.CharField(max_length=20, null=True)
    term = models.PositiveIntegerField(choices=settings.TERM_CHOICES, null=True)
    year = models.CharField(max_length=4, null=True)
    school_id = models.CharField(max_length=20, null=True)
    school_token = models.ForeignKey('payments.AccessToken', null=True)
    validated = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "(%s, %s)" % (self.student, self.access_code)

    class Meta:
        unique_together = ('student', 'term', 'year')
        ordering = ('-date_created',)

    def save(self, **kwargs):
        if not self.access_code:
            self.access_code = 'PIN-'+pin_generator(length=10)
        super(AccessCard, self).save(**kwargs)



class AccessToken(models.Model):
    token = models.CharField(max_length=30, null=True, blank=True)
    token_application = models.ForeignKey('payments.TokenApplication')
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s: (%s)' % (self.token, self.school)

    class Meta:
        ordering = ('-date_created',)

    def save(self, **kwargs):
        if not self.token:
            self.token = 'TOKEN-'+pin_generator(length=15)
        super(AccessToken, self).save(**kwargs)


class TokenApplication(models.Model):
    STATUS = (
        ('I', 'Initialized'),
        ('A', 'Approved'),
        ('P', 'Processing'),
        ('D', 'Declined'),
        ('C', 'Cancelled')
    )
    NAIRA = 'Naira'
    DOLLARS = 'Dollars'

    PAYMENT_CURRENCY = (
        (NAIRA, "Naira"),
        (DOLLARS, "Dollars"),
    )

    GTPAY = 'GTPay'
    PAYPAL = 'PayPal'
    PAYSTACK = 'Paystack'
    TELLER = 'Teller'

    PAYMENT_METHOD = (
        (GTPAY, "GTPay"),
        (PAYSTACK, 'Paystack'),
        (PAYPAL, 'Paypal'),
        (TELLER, 'Bank Transfer/Teller'),
    )
    application_id = models.CharField(max_length=30, null=True)
    school = models.ForeignKey('institutions.Institution', null=True)
    year = models.CharField(max_length=4, null=True)
    term = models.PositiveIntegerField(choices=settings.TERM_CHOICES, null=True)
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(editable=False, max_length=50, choices=PAYMENT_METHOD, null=True)
    payment_id = models.CharField(max_length=21, null=True)
    status = models.CharField(max_length=1, choices=STATUS, default='I')
    date_created = models.DateTimeField(auto_now_add=True)
    # the fields below are optional. They vary based on the payment method
    teller_number = models.CharField(max_length=20, null=True,blank=True)
    teller_date = models.DateField(null=True,blank=True)


    def __str__(self):
        return '%s --> %s' % (self.school, self.application_id)

    class Meta:
       ordering = ('-date_created',)

    def save(self, **kwargs):
        if not self.payment_id:
            self.payment_id = 'SANI_PAY_'+pin_generator(length=10)
            self.application_id = 'SANI_APPLY_'+pin_generator(length=10)
        super(TokenApplication, self).save(**kwargs)

    @property
    def get_token(self):
        access_token = AccessToken.objects.get(token_application=self)
        return access_token.token

    @property
    def get_status(self):
        status = {'I': 'Initialized', 'A': 'Approved', 'P': 'Processing', 'D': 'Declined', 'C': 'Cancelled'}
        return status[self.status]

    @property
    def get_term(self):
        terms = {1:'First Term', 2:'Second Term', 3:'Third Term'}
        return terms[self.term].upper()


class Plan(models.Model):
    name = models.CharField(max_length=50)
    plan_code = models.CharField(max_length=25, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=10, default=0.0)
    student_limit = models.PositiveIntegerField(default=0)
    staff_limit = models.PositiveIntegerField(default=0)
    result_limit = models.PositiveIntegerField(default=0)
    max_admin = models.PositiveIntegerField(default=1)

    def __str__(self):
        return "%s - %s" % (self.name, self.plan_code)

    @property
    def amount_in_kobo(self):
        return int(self.amount * 100)


class Subscription(models.Model):
    customer = models.ForeignKey("institutions.Institution")
    active = models.BooleanField(default=True)
    subscription_code = models.CharField(max_length=25)
    plan = models.ForeignKey(Plan)
    subscribed_on = models.DateTimeField()

    def __str__(self):
        return self.subscription_code

    def disable_subscription(self):
        self.active = False
