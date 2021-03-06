import os
from rave_api.errors import MissingAuthorizationKeyError, InvalidDataError, InvalidCardTypeError
from django.contrib.auth.models import User
import random
try: 
    import json
except:
    import simplejson as json


class BaseRaveAPI(object):
    _CONTENT_TYPE = 'application/json'
    _TEST_BASE_ENDPOINT = 'https://ravesandboxapi.flutterwave.com/flwv3-pug/getpaidx/api/'
    _LIVE_BASE_ENDPOINT = 'https://api.ravepay.co/flwv3-pug/getpaidx/api/'
    
    def __init__(self, is_live=False, flutterwave_secret_key=None):
        self._live = is_live
        if not flutterwave_secret_key:
            self._MERCHANT_SECRET_KEY = os.environ.get('RAVE_SECRET_KEY', 'FLWSECK-b261ce10e4200564fa800b728ce42001-X')
        else:
            self._MERCHANT_SECRET_KEY = flutterwave_secret_key
        if not self._MERCHANT_SECRET_KEY:
            self._MERCHANT_SECRET_KEY = ''
    
    def _get_base_endpoint(self):
        """
        This returns the base endpoint for the specified 
        use case i.e. Live or a Sandbox account
        """
        if self._live:
            return self._LIVE_BASE_ENDPOINT
        return self._TEST_BASE_ENDPOINT
    
    def _url(self, path):
        """
        Returns an absolute URL for a particular api endpoint

        ARGS:
            STRING:PATH = relative path to the api
        """
        return self._get_base_endpoint() + path
    
    def _get_key(self):
        """
        Return the marchant's secrete_key
        """
        return self._MERCHANT_SECRET_KEY

    def _get_payload(self, data_payload):
        """set the payload for the rave transaction
        
        ARGS:
            OBJECT:data_payload = instance of BasePayloader with the various 
            fields for the rave parameter
        """
        return data_payload.json_payload()
   
    def _headers(self):
        """Returns a simple header that will be added to the request payload"""
        return {
            "Content-Type": self._CONTENT_TYPE,
        }
    
    def _handle_request(self, method, url, encrypted_payload=None):
        """Handles all requests: GET, POST, PUT, DELETE etc"""
        raise NotImplementedError("This method needs to be implemented")

    def _get_encrypt_key(self):
        """
        this is the getKey function that generates an encryption Key 
        for you by passing your Secret Key as a parameter.
        """
        raise NotImplementedError("This method needs to be implemented")

    def encrypt_data(self, key, plainText):
         """
         This is the encryption function that encrypts your 
         payload by passing the text and your encryption Key.
         """
         raise NotImplementedError("This method needs to be implemented")
    
    def initialize(self):
        raise NotImplementedError("This method needs to be implemented")
    
    def verify_card_type(self):
        raise NotImplementedError("This method needs to be implemented")
    
    def _local_card_validation(self):
        raise NotImplementedError("This method needs to be implemented")
    
    def _foreign_card_validation(self):
        raise NotImplementedError("This method needs to be implemented")
    
    def validate(self):
        raise NotImplementedError("This method needs to be implemented")
    
    def verify(self):
        raise NotImplementedError("This method needs to be implemented")
    

class BasePayloader:

    def __init__(self, amount, user, card, PBFPubKey, ip_address, **kwargs):
        if not user and not isinstance(user, User):
            raise InvalidDataError("Customer needs to register before making purchase")
        if not card and not isinstance(card, Card):
            raise InvalidDataError("Customer needs a valid card to initiate this transaction")
        
        self.PBFPubKey = PBFPubKey
        self.firstname = user.first_name
        self.lastname = user.last_name
        self.amount = amount
        self.IP = ip_address
        self.email = user.email
        self.cardno = card.get_number()
        self.cvv = card.get_cvv()
        self.expirymonth, self.expiryyear = card.get_expiration_details()
    
    def update_payload(self, **kwargs):
        """Adding optional data fields to the payload"""
        existing_payload = self.__dict__
        new_payload = existing_payload.update(kwargs)

    def _to_json(self):
        """convert this object to a json representation for easy processing 
        """
        return json.dumps(self.__dict__)
    
    def json_payload(self):
        return self._to_json()
    
    def _decode_json(self):
        return json.loads(self._to_json())

    def _get_transaction_reference(self):
        return self._generate_code(width=10)
    
    def _generate_code(self, width=4, prefix='RAVEIT-'):
        alpha_list = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        num_list = '1234567890'
        lower_alpha_list = alpha_list.lower()
        generator_base = [alpha_list, lower_alpha_list, num_list]

        key_list = ''.join(generator_base)
        token = prefix+''

        for _ in range(width):
            token += key_list[random.randint(1,len(key_list)-1)]
        return token
    

        
class Card:
    
    def __init__(self, cardno, cvv, expiry_month, expiry_year):
        self._cvv = cvv
        self._cardno = cardno
        self._expiry_month = expiry_month
        self._expiry_year = expiry_year 
    
    def get_cvv(self):
        return self._cvv
    
    def get_number(self):
        return self._cardno
   
    def get_expiration_details(self):
        return self._expiry_month, self._expiry_year