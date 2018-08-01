from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from rave_api.base import BaseRaveAPI, Card, BasePayloader
from django.contrib.auth.models import User
import os
from rave_api.transactions import Transaction

class BaseAPITest(TestCase):

    default_instance = BaseRaveAPI()
    def test_base_test_endpoint_url(self): 
        """Test for the base test endpoint url of rave"""
        base_instance = BaseRaveAPI()
        self.assertEqual(base_instance._get_base_endpoint(), 'https://ravesandboxapi.flutterwave.com/flwv3-pug/getpaidx/api/')
    
    def test_base_test_endpoint_url_with_path(self, path='charge'): 
        """Test for the base test endpoint url of rave with path"""
        base_instance = BaseRaveAPI()
        self.assertEqual(base_instance._url(path), 'https://ravesandboxapi.flutterwave.com/flwv3-pug/getpaidx/api/charge')
    
    def test_base_live_endpoint_url(self, path='charge'): 
        """Test for the base live endpoint url of rave with path"""
        base_instance = BaseRaveAPI(is_live=True)
        self.assertEqual(base_instance._url(path), 'https://api.ravepay.co/flwv3-pug/getpaidx/api/charge')
    
    def test_secrete_key_exist_and_valid(self):
        """test if the secrete key exists"""
        key_exists = self.default_instance._get_key() is not ''
        key = self.default_instance._get_key()
        # self.assertEqual(key_exists, False)
        self.assertEqual(key[:8], 'FLWSECK-')
    
    def test_payload(self):
        """test to make sure the payload is an instance of Payload class"""
        
pin = 3310
otp = 12345
card = Card('5399 8383 8383 8381', '470', '10', '22') # Card instance
class CardTest(TestCase):
    
    def test_card_is_valid(self):
        """Tests for the validity of the card"""
    
        self.assertEqual(card.get_cvv(), '470') # Ge the cvv number
        self.assertEqual(card.get_number(), '5399 8383 8383 8381') # Ge the card number
        self.assertEqual(card.get_expiration_details(), ('10', '22')) # Ge the expiration details


class PayloadTest(TestCase):
    def setUp(self):
        User.objects.create_user('nule@gmail.com', email='nule@gmail.com', password='nule@gmail.com', first_name='Nule', last_name='Well')
        self.user = User.objects.get(pk=1)

    def test_data_validity(self):
        payload = BasePayloader(2300, self.user, card, 'FLWPUBK-18b01b5b8141e1f22eb166759ae7c064-X')
        self.assertEqual(payload._get_transaction_reference()[:4], 'RAVE')
        self.assertEqual(payload.email, 'nule@gmail.com')
        self.assertEqual(type(payload._to_json()), str)
        self.assertEqual(payload._decode_json(), payload.__dict__)
    
    def test_update_payload(self):
        payload = BasePayloader(2300, self.user, card, 'FLWPUBK-18b01b5b8141e1f22eb166759ae7c064-X')
        added_data = {'pin': pin, 'suggested_auth': 'PIN'}
        payload.update_payload(**added_data)
        self.assertEqual(payload.__dict__['suggested_auth'], 'PIN')


class TransactionTest(TestCase):
    def setUp(self):
        User.objects.create_user('nule54@gmail.com', email='nule54@gmail.com', password='nule54@gmail.com', first_name='Nulepu', last_name='Well')
        self.user = User.objects.get(pk=1)
        self.payloader = BasePayloader(2300, self.user, card, 'FLWPUBK-18b01b5b8141e1f22eb166759ae7c064-X')
        self.tx = Transaction(flutterwave_secret_key='FLWPUBK-18b01b5b8141e1f22eb166759ae7c064-X')

    def test_encrytion_key(self):
        self.assertEqual(self.tx._get_encrypt_key()[:7], 'FLWPUBK')
    
    def test_encryted_payload(self):
        encrypted_data = self.tx.encrypt_data(self.payloader)
        self.assertEqual(encrypted_data['alg'], "3DES-24")
    
    def test_initialize(self):
        response = self.tx.initialize(self.payloader)
        self.assertEqual(response, 'PIN')


