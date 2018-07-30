from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^application$', apply, name='apply'),
    url(r'^list$', PaymentListView.as_view(), name='list'),   
    url(r'^tokens/$',generate, name='generate'),   
    url(r'^pin/print/(?P<token>[\w-]+)$', print_tokens, name='print'),   
    url(r'^cancel/(?P<payment_id>[\w-]+)$',cancel_payment, name='cancel'),   
    url(r'^search/$',search, name='search'),   
    url(r'^api$',search_api, name='search-json'),   
    url(r'^new$',new_pin, name='new'),   
    url(r'^json-pin$',json_pin, name='json-pin'),   
    url(r'^validate$',validation, name='validate'),   
    url(r'^validate/pin$',get_validated_pin, name='json-validate'),   
    url(r'^pay$',make_payment, name='pay'),   
    url(r'^checkout/(?P<payment_id>[\w-]+)$',initiate_payment, name='initialize'),   
    url(r'^payment_confirmed$',payment_confirmed, name='confirmed'),   
    url(r'^token_without_pay/(?P<payment_id>[\w-]+)$',activate_without_pay, name='without-pay'),   
    url(r'^teller-pay/(?P<payment_id>[\w-]+)$',teller_pay, name='teller-pay'),   
]