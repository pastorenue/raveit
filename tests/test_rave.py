from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from rave_api.base import BaseRaveAPI, Card, BasePayloader
from django.contrib.auth.models import User
import os

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
        

card = Card('123456789', '234', '12', '20') # Card instance
class CardTest(TestCase):
    
    def test_card_is_valid(self):
        """Tests for the validity of the card"""
    
        self.assertEqual(card.get_cvv(), '234') # Ge the cvv number
        self.assertEqual(card.get_number(), '123456789') # Ge the card number
        self.assertEqual(card.get_expiration_details(), ('12', '20')) # Ge the expiration details


class PayloadTest(TestCase):
    def setUp(self):
        User.objects.create_user('nule@gmail.com', email='nule@gmail.com', password='nule@gmail.com', first_name='Nule', last_name='Well')


    def test_data_validity(self):
        user = User.objects.get(pk=1)
        payload = BasePayloader(2300, user, card, 'FLWPUBK-18b01b5b8141e1f22eb166759ae7c064-X')
        self.assertEqual(payload._get_transaction_reference()[:4], 'RAVE')
        self.assertEqual(payload.email, 'nule@gmail.com')
        self.assertEqual(type(payload._to_json()), str)
        self.assertEqual(payload._decode_json(), payload.__dict__)


