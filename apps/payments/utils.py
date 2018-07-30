from payments.models import AccessCard, AccessToken
from config.utils import pin_generator
from students.models import Student
import requests
import webbrowser
import os
try:
    import simplejson as json
except:
    import json

def tokens(school_token, school,year,term):
    students = Student.objects.filter(school=school)
    result = None
    access_token = AccessToken.objects.filter(token=school_token.token)
    #check if the token already exists
    if access_token.exists():
        access_token = access_token[0]
        if access_token.token_application.year != year:
            return False
        if access_token.token_application.term != int(term):
            return False
        try:
            for student in students:
                AccessCard.objects.create(
                    student=student,
                    access_code='PIN-'+pin_generator(length=12),
                    term=access_token.token_application.term,
                    year=access_token.token_application.year,
                    school_id=school.registration_id,
                    school_token=access_token
                )
            result = True
        except Exception as e:
            raise ValueError(e)
    return result


class PaystackTransaction:

    def __init__(self, api_url='https://api.paystack.co/', secret_key=None):
        self._base_url = api_url
        self._key = secret_key
        if secret_key:
            self._base_url = api_url
        else:
            try:
                self._key = os.environ.get('PAYSTACK_SECRET_KEY', 'sk_test_2757e92b4cd26e9b5d54f361b8b4dec3e6ec410d')
            except Exception as e:
                raise ValueError(e)
        self._CONTENT_TYPE = "application/json"
        self.authorization_url = None
    
    def _url(self, path):
        return self._base_url + path

    def _headers(self):
        return { 
                "Content-Type": self._CONTENT_TYPE, 
                "Authorization": "Bearer " + self._key
                }
    
    def _handle_request(self, method, url, data=None):
        try:
            response = requests.request(method, url, headers=self._headers(), data=data)
            if response.json().get('status'):
                return response
        except Exception as e:
            raise ValueError(e)
    
    def initialize(self, email, amount, reference=None, callback_url=None):
        """
        Initialize a transaction and returns the response
        
        ARGS:
        email --> Customer's email address
        amount --> Amount to charge
        plan --> optional
        Reference --> optional
        """

        if not email:
            raise InvalidDataError("Customer's Email is required for initialization") 

        if reference:
            reference = "_".join(reference.split('-'))
        url = self._url("/transaction/initialize")
        payload = {
                    "email":email,
                    "amount": amount,
                    "callback_url": "{}".format(callback_url),
                    "reference": reference
                }
        response = self._handle_request("post", url, json.dumps(payload)).json()
        self.authorization_url = response['data'].get('authorization_url')
        return response

    def charge(self, email, auth_code, amount, reference=None):
        """
        Charges a customer and returns the response
        
        ARGS:
        auth_code --> Customer's auth code
        email --> Customer's email address
        amount --> Amount to charge
        reference --> optional
        """

        if not email:
            raise InvalidDataError("Customer's Email is required to charge")

        if not auth_code:
            raise InvalidDataError("Customer's Auth code is required to charge") 
        
        url = self._url("/transaction/charge_authorization")
        payload = {
                    "authorization_code":auth_code, 
                    "email":email, 
                    "amount": amount,
                    "reference": reference
                }
        data = json.dumps(payload)
        return self._handle_request('POST', url, data)

    def verify(self, reference):
        """
        Verifies a transaction using the provided reference number

        args:
        reference -- reference of the transaction to verify
        """
        
        reference = str(reference)
        url = self._url("/transaction/verify/{}".format(reference))
        return self._handle_request('GET', url)

    def authorize(self, auth_url=None):  # pragma: no cover
        """
        Open a browser window for client to enter card details.
        Args:
            auth_url (string, optional): Paystack verified authorization_url
        Raises:
            e: Browser Error :(
            error.ValidationError: Bad input.
        Returns:
            None
        """
        if not auth_url and not self.authorization_url:
            raise error.ValidationError('This transaction object does not'
                                        ' have an authorization url.You must'
                                        ' provide an authorization url or'
                                        'for call the `initialize` method'
                                        ' this transaction first.')

        authorization_url = (
            lambda auth_url: auth_url if auth_url else self
            .authorization_url)(auth_url)

        try:
            webbrowser.open(authorization_url, new=0, autoraise=True)
        except webbrowser.Error as e:
            raise e