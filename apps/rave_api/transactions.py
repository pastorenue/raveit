from .base import BaseRaveAPI # pylint: disable=E0401
import requests
import random
import base64
import hashlib
from cryptography.fernet import Fernet # pylint: disable=E0401
from .errors import RaveAPIError, InvalidDataError
try:
    import json
except:
    import simplejson as json

class Transaction(BaseRaveAPI):
    
    def _handle_request(self, method, url, encrypted_payload=None):
        """Handles all requests: GET, POST, PUT, DELETE etc"""
        if not encrypted_payload:
            raise InvalidDataError("Error: You need to pass a valid payload")
        try:
            payload = json.dumps(encrypted_payload)
            response = requests.request(method, url, headers=self._headers(), data=payload)
            return response
        except Exception as e:
            raise ValueError(e)
    
    def _get_encrypt_key(self):
        """Implementing the getEncryptKey() from the base class"""
        seckey = self._get_key()
        hashedseckey = hashlib.md5(seckey.encode("utf-8")).hexdigest()
        hashedseckeylast12 = hashedseckey[-12:]
        seckeyadjusted = seckey.replace('FLWSECK-', '')
        seckeyadjustedfirst12 = seckeyadjusted[:12]
        return seckeyadjustedfirst12 + hashedseckeylast12
    
    def encrypt_data(self, payloader):
        """Implementing the encrypt_data() from base class"""
        blockSize = 8
        plain_text = payloader.json_payload()
        padDiff = blockSize - (len(plain_text) % blockSize) # Using this line as specified by the rave docs
        plain_text = "{}{}".format(plain_text, "".join(chr(padDiff) * padDiff))
        #key = self.get_encrypt_key()
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        encrypted_data = base64.b64encode(cipher_suite.encrypt(str.encode(plain_text)))
        return {
            "PBFPubKey": self._get_key(),
            "client": encrypted_data,
            "alg": "3DES-24"
        }

    def initialize(self, payloader):
        """Implement the base class to initialize the payment
        
        DESCRIPTION
            METHOD: 'post'
            ENDPOINT: 'charge'
        
        RETURNS
            response (dict): api response depending on card of the customer
        """
        endpoint = 'charge'
        method = 'POST'
        url = self._url(endpoint)
        payload = self.encrypt_data(payloader)
        
        # process the transaction
        response = self._handle_request(method, url, payload)
        if not response.get('status', False):
            raise RaveAPIError("There is a problem with your API configuration.\
                            contact Pastor, Emmanuel on pastorenuel@gmail.com")
        return response

