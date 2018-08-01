from .base import BaseRaveAPI # pylint: disable=E0401
import requests
import random
import base64
import hashlib
#from cryptography.fernet import Fernet # pylint: disable=E0401
from Cryptodome.Cipher import DES3
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
            response = requests.request(method, url, headers=self._headers(), data=json.dumps(encrypted_payload))
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
        key = self._get_encrypt_key()
        plain_text = payloader.json_payload()
        padDiff = blockSize - (len(plain_text) % blockSize) # Using this line as specified by the rave docs
        cipher_suite = DES3.new(key, DES3.MODE_ECB)
        plain_text = "{}{}".format(plain_text, "".join(chr(padDiff) * padDiff)).encode("utf8")
        encrypted_data = base64.b64encode(cipher_suite.encrypt(plain_text))

        data =  {
            'PBFPubKey': self._get_key(),
            'client': encrypted_data.decode("utf8"),
            'alg': '3DES-24'
        }
        return data

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
        try:
            response = self._handle_request(method, url, encrypted_payload=payload)
            import pdb; pdb.set_trace()
            if not response.get('status', False):
                raise RaveAPIError("There is a problem with your API configuration.\
                                contact Pastor, Emmanuel on pastorenuel@gmail.com")
        except Exception as e:
            raise ValueError(e)
        return response

