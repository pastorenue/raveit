from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from .models import TokenApplication, AccessCard, AccessToken
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import datetime
from .forms import ApplicationForm, TellerPaymentForm
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from .utils import tokens, PaystackTransaction as Transaction
from reports.utils import render_to_pdf as rtp
from students.models import Student
from django.contrib.humanize.templatetags.humanize import ordinal
from config.utils import pin_generator
from config.models import Config

#from paystackapi.transaction import Transaction
try:
    import simplejson as json
except:
    import json

# Create your views here.
class PaymentListView(ListView):
    model = TokenApplication
    template_name = 'payments/list.html'
    paginated_by = settings.PAGE_SIZE

    def get_queryset(self):
        teacher = self.request.user.teacher
        queryset = super(PaymentListView, self).get_queryset().filter(school=teacher.school)
        params = self.request.GET
        year = params.get('year','all')
        term = params.get('term','all')

        if year !='all':
            queryset = queryset.filter(year=year)
        if term !='all':
            queryset = queryset.filter(term=term)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(PaymentListView, self).get_context_data(**kwargs)
        payments = self.get_queryset()
        paginator = Paginator(payments, self.paginated_by)

        page = self.request.GET.get('page')

        try:
            payments = paginator.page(page)
        except PageNotAnInteger:
            payments  = paginator.page(1)
        except EmptyPage:
            payments = paginator.page(paginator.num_pages)
        context['payments'] = payments
        context['years'] = [i for i in range(datetime.date.today().year, datetime.date.today().year-20, -1)]
        return context
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentListView, self).dispatch(request, *args, **kwargs)

@login_required
@user_passes_test(lambda u: hasattr(u, 'teacher'), login_url='/auth/login/')
def apply(request):
    template_name = 'payments/apply.html'
    school = request.user.teacher.school
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        t_application = TokenApplication.objects.filter(
                            school=school,
                            term=request.POST.get('term'),
                            year=request.POST.get('year'))
        if t_application.filter(status='A').exists():
            messages.error(request, 'You already have an existing token for this year and term')
            return HttpResponseRedirect(reverse('payments:apply'))
        if t_application.filter(status='I').exists():
            messages.error(request, 'Sorry! You already have this token pending for processing')
            return HttpResponseRedirect(reverse('payments:apply'))
        if form.is_valid():
            application = form.save(commit=False)
            application.school = request.user.teacher.school
            application.save()
            messages.info(request, "Your application is been processed. Track the progress with Payment ID:'%s'" % (application.application_id))
            return HttpResponseRedirect(reverse('payments:list'))
    else:
        form = ApplicationForm()
    context = {'form': form}
    return render(request, template_name,context)

@login_required
@user_passes_test(lambda u: hasattr(u, 'teacher'), login_url='/auth/login/')
def generate(request):
    template_name = 'payments/generate_tokens.html'
    years = [i for i in range(datetime.date.today().year, datetime.date.today().year-20, -1)]
    if request.method == 'POST':
        params = request.POST
        token = params.get('token')
        year = params.get('year')
        term = params.get('term')
        teacher = request.user.teacher
        response = tokens(token, teacher.school, year, term)
        if response:
            messages.success(request, "Access Tokens were successfully generated for all students in your school")
            HttpResponseRedirect(reverse('payments:print'))
    return render(request, template_name, {'years': years})

@login_required
@user_passes_test(lambda u: hasattr(u, 'teacher'), login_url='/auth/login/')
def cancel_payment(request, payment_id):
    payment_application = get_object_or_404(TokenApplication, payment_id=payment_id)
    payment_application.status = 'C'
    payment_application.save()
    return HttpResponseRedirect(reverse('payments:list'))


@login_required
@user_passes_test(lambda u: hasattr(u, 'teacher'), login_url='/auth/login/')
def print_tokens(request, token):
    template_name = 'payments/print_tokens.html'
    current_user = request.user.teacher
    context = {}
    access_token = get_object_or_404(AccessToken, token=token)

    access_cards = AccessCard.objects.filter(school_token=access_token).prefetch_related('student')
    if access_cards.exists():
        context['access_cards'] = access_cards
        context['school'] = current_user.school
        context['token'] = access_token
    else:
        #get access card for this token
        response = tokens(access_token, current_user.school,
        access_token.token_application.year, access_token.token_application.term)
        if response:
            access_cards = AccessCard.objects.filter(school_token=access_token)
            context['access_cards'] = access_cards
            context['school'] = current_user.school
        context['token'] = access_token
    return rtp(template_name, context)


@login_required
@user_passes_test(lambda u: hasattr(u, 'teacher'), login_url='/auth/login/')
def search(request):
    return render(request, 'payments/search_pin.html', {})


def search_api(request):
    data = {}
    params = request.GET
    reg_number = params.get('reg_number')
    year = params.get('year')
    term = params.get('term')

    try:
        student = get_object_or_404(Student, reg_number=reg_number)
        access_card = AccessCard.objects.filter(student=student, year=year, term=term)
        if access_card.exists():
            access_card = access_card[0]
            data['pin'] = access_card.access_code
            data['name'] = access_card.student.full_name
            data['reg_number'] = access_card.student.reg_number
            data['class'] = "{}-{}".format(access_card.student.student_class.caption, access_card.student.student_class.nick_name)
            data['message'] = 'Success!'
            data['status_code'] = 1
        else:
            data['message'] = 'No pin Available'
    except:
        data['message'] = "There was no pin found for student with Reg Number: '%s'" % (reg_number)
    return HttpResponse(json.dumps(data), content_type="application/json")


@login_required
@user_passes_test(lambda u: u.teacher.is_admin, login_url='/auth/login/')
def new_pin(request):
    template_name = 'payments/new_pin.html'
    context = {
        'years': [i for i in range(datetime.date.today().year, datetime.date.today().year-5, -1)]
    }
    return render(request, template_name, context)


@login_required
@user_passes_test(lambda u: u.teacher.is_admin, login_url='/auth/login/')
def json_pin(request):
    data = {}
    params = request.GET
    school_token = params.get('token')
    reg_number = params.get('reg_number')
    school = request.user.teacher.school

    access_token = AccessToken.objects.filter(token=school_token)
    if access_token.exists():
        access_token = access_token[0]
        try:
            student = get_object_or_404(Student, reg_number=reg_number)
            #Lets be sure there's no pin for this student
            access_card = AccessCard.objects.filter(student=student, year=access_token.year, term=access_token.term)
            if access_card.exists():
                data['message'] = 'This student already has a pin for %s Term, %s' % (ordinal(term), year)
            else:
                access_card = AccessCard.objects.create(
                        student=student,
                        access_code='PIN-'+pin_generator(length=12),
                        term=access_token.term,
                        year=access_token.year,
                        school_id=school.registration_id,
                        school_token=access_token
                    )
                data['pin'] = access_card.access_code
                data['name'] = access_card.student.full_name
                data['reg_number'] = access_card.student.reg_number
                data['class'] = "{}-{}".format(access_card.student.student_class.caption, access_card.student.student_class.nick_name)
                data['message'] = 'Success!'
                data['status_code'] = 1
        except:
            data['message'] = "There's No Student with Reg Number: '%s'" % (reg_number)
    else:
        data['message'] = "Oops! It seem you're using a wrong token: %s. Contact SANI for help" % (school_token)
    return HttpResponse(json.dumps(data), content_type="application/json")


@login_required
@user_passes_test(lambda u: hasattr(u, 'student'), login_url='/auth/login/')
def validation(request):
    template_name = 'payments/validate.html'
    return render(request, template_name, {})


@login_required
@user_passes_test(lambda u: hasattr(u, 'student'), login_url='/auth/login/')
def get_validated_pin(request):
    params = request.GET
    data = {}
    access_code = params.get('token')
    try:
        access_card =AccessCard.objects.filter(student=request.user.student, access_code=access_code)
        access_card = access_card[0]
        access_card.validated = True
        access_card.save()
        #return json data
        data['status_code'] = 1
        data['message'] = 'Congratulations! Your pin has been validated and your account now fully ACTIVE'
        data['pin'] = access_card.access_code
        data['name'] = access_card.student.full_name
        data['reg_number'] = access_card.student.reg_number
        data['class'] = "{}-{}".format(access_card.student.student_class.caption, access_card.student.student_class.nick_name)
    except:
        data['message'] = 'Sorry! You pin did not validate. Meet your school for a valid pin number'
    return HttpResponse(json.dumps(data), content_type="application/json")


@login_required
def initiate_payment(request, payment_id):
    school = request.user.teacher.school
    config = Config.objects.get(school=school)
    application = get_object_or_404(TokenApplication, payment_id=payment_id)
    school = request.user.teacher.school
    pay_root = payment_id.split('_')[2]
    students = Student.objects.filter(school=school, user_status='A')
    amount = float(students.count() * config.plan.amount)
    context = {
        'amount': amount,
        'pay_root': pay_root,
        'email': request.user,
        'school': school,
        'application': application

    }
    return render(request, 'payments/api_pay.html', context)


@login_required
def make_payment(request):
    school = request.user.teacher.school
    config = Config.objects.get(school=school)
    school = request.user.teacher.school
    students = Student.objects.filter(school=school, user_status='A')
    email = request.user.username
    amount = float(students.count() * config.plan.amount * 100)
    reference = request.POST.get('pay')

    transaction = Transaction(secret_key=settings.PAYSTACK_API_KEY)
    response = transaction.initialize(email, amount, reference,
                        callback_url="http://localhost:2012/payments/payment_confirmed")
    transaction.authorize()

    print(response)
    return HttpResponseRedirect(reverse('dashboard'))
   # except Exception as e:
    messages.error(request, "An error has just occured. It seem you have problems with your connection. "
        "Try the action after a while")
    return HttpResponseRedirect(reverse('payments:list'))


@login_required
def payment_confirmed(request):
    reference_code = request.GET.get('reference')
    reference = "-".join(reference_code.split('_'))
    p = Transaction(secret_key=settings.PAYSTACK_API_KEY)
    response = p.verify(reference_code).json()
    tokenApp = TokenApplication.objects.get(payment_id=reference)
    tokenApp.status = "A"
    tokenApp.is_paid = True
    tokenApp.save()

    activate_token(tokenApp)
    context = {
        "token_app": tokenApp,
        "response": response['data'],
        "amount": "%.2f" % (response['data'].get('amount')/100)
    }
    return render(request, 'payments/confirmed.html', context)

def req(amount, email, reference):
    import requests
    import webbrowser
    payload={
        "email": "{}".format(email),
        "amount": amount,
        "reference": "{}".format(reference),
        "callback_url": "http://localhost:2012/auth/dashboard"
    }
    data = json.dumps(payload)
    headers={
        "Authorization": "Bearer sk_test_2757e92b4cd26e9b5d54f361b8b4dec3e6ec410d",
        "Content-Type": "application/json"
    }
    url = "https://api.paystack.co/transaction/initialize"
    return requests.request("post", url,
        headers=headers,
        json=payload
    )
    #webbrowser.open(response['data']['authorization_url'])

def activate_token(token_application):
    try:
        access_token = AccessToken.objects.get(token_application=token_application)
    except:
        AccessToken.objects.create(
            token_application=token_application,
        )

def activate_without_pay(request, payment_id):
    tokenApp = TokenApplication.objects.get(payment_id=payment_id)
    tokenApp.status = "A"
    tokenApp.is_paid = True
    tokenApp.save()

    activate_token(tokenApp)
    return HttpResponseRedirect(reverse('payments:list'))

def teller_pay(request, payment_id):
    tokenApp = TokenApplication.objects.get(payment_id=payment_id)
    context = {}
    template_name = 'payments/teller.html'
    if request.method == 'POST':
        form = TellerPaymentForm(request.POST)
        if form.is_valid():
            tokenApp.teller_number = form.cleaned_data['teller_number']
            tokenApp.teller_date = form.cleaned_data['teller_date']
            tokenApp.payment_method = 'Teller'
            tokenApp.status = 'P'
            tokenApp.save()
            messages.info(request, "The Transaction is processing. Your payment will be verified within 48hours")
            return HttpResponseRedirect(reverse('payments:list'))
    else:
        context['form'] = TellerPaymentForm()
        context['token_app'] = tokenApp
    return render(request, template_name, context)
