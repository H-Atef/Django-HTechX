

from subscriptions.helpers.paypal_subscription import PayPalClient
from subscriptions.helpers.stripe_subscription import StripeClient
from subscriptions.helpers.base_subscription import BaseClient

class SubscriptionContext:

    def __init__(self,payment_method="paypal"):
        self.payment_clients={
            "paypal":PayPalClient(),
            "stripe":StripeClient()
        }
        self.payment_method=payment_method
        self.payment_client:BaseClient=None

    def initialize_payment_client(self,payment_method:str=None):
        if not payment_method:
            self.payment_client=self.payment_clients[self.payment_method]
            return self.payment_client
        else:
            self.payment_client=self.payment_clients[payment_method]
            return self.payment_client
        

     
    def create_subscription(self,user):
        if self.payment_client:
            return self.payment_client.create_subscription(user)
        else:
            return {"error":"Payment Client Not Initialized"}
        
    def cancel_subscription(self,user):
        if self.payment_client:
            return self.payment_client.cancel_subscription(user)
        else:
            return {"error":"Payment Client Not Initialized"}
        
    def excute_subscription(self,request):
        if self.payment_client:
            return self.payment_client.excute_subscription(request)
        else:
            return {"error":"Payment Client Not Initialized"}

  