from django import forms
import datetime
from .models import TokenApplication


class ApplicationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ApplicationForm, self).__init__(*args, **kwargs)
        self.fields['year'].widget.attrs = {'class': 'form-control input-sm in-search'}
        self.fields['year'].queryset = [i for i in range(datetime.date.today().year, datetime.date.today().year-20, -1)]
        self.fields['term'].widget.attrs = {'class': 'form-control input-sm in-search'}
    
    class Meta:
        model = TokenApplication
        fields = ('year', 'term')

class TellerPaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TellerPaymentForm, self).__init__(*args, **kwargs)
        self.fields['teller_number'].widget.attrs = {'class': 'form-control input-sm in-search'}
        self.fields['teller_date'].widget.attrs = {'class': 'form-control input-sm in-search'}

    class Meta:
        model = TokenApplication
        fields = ('teller_number', 'teller_date')