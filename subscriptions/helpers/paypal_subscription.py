
from django.conf import settings
from django.utils.timezone import timedelta
import paypalrestsdk.api
from subscriptions.models import Subscription
import paypalrestsdk
from subscriptions.helpers.base_subscription import BaseClient
from urllib.parse import urlparse, parse_qs
from django.utils import timezone
from profiles.models import Profile


paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})

class PayPalClient(BaseClient):

    def _extract_token(self,url):
        """Extracts the PayPal token from the checkout URL."""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return query_params.get("token", [None])[0]  

    def _get_existing_plan(self):
        """Retrieve an existing PayPal subscription plan."""
        try:
            plans = paypalrestsdk.BillingPlan.all({"status": "ACTIVE"})
            if plans and len(plans["plans"]) > 0:
                return plans["plans"][0]["id"]  
        except Exception as e:
            return None 
        return None

 
    def _create_plan(self):
        """Create a PayPal subscription plan if not already created."""
        try:
            # Step 1: Check if an active plan already exists
            existing_plan_id = self._get_existing_plan()
            if existing_plan_id:
                return existing_plan_id  # Return existing plan ID

            # Step 2: Create a new PayPal plan
            plan = paypalrestsdk.BillingPlan({
                "name": "HTech Premium Monthly Subscription Plan",
                "description": "Subscription plan for users",
                "type": "fixed",
                "payment_definitions": [{
                    "name": "Premium Plan",
                    "type": "REGULAR",
                    "frequency": "MONTH",
                    "frequency_interval": "1",
                    "amount": {"currency": "USD", "value": "2.00"},
                    "cycles": "1"
                }],
                "merchant_preferences": {
                    "setup_fee": {"currency": "USD", "value": "2.00"},
                    "return_url": "http://localhost:8000/api/v1/subscription/paypal/execute/",
                    "cancel_url": "http://localhost:8000/api/v1/subscription/cancel-url/",
                    "auto_bill_amount": "YES",
                    "initial_fail_amount_action": "CONTINUE"
                }
            })

            if plan.create():
                plan.activate()
                return plan.id
                

            return plan.error  # Failed to create plan
        except Exception as e:
            return None  # Log the error if needed
        
   
    def create_subscription(self,user):
        """Create PayPal subscription checkout session."""
        try:
            # Step 1: Check if user already has an active or refunded subscription
            subscription = Subscription.objects.filter(user=user).first()

            if subscription:
                if subscription.status == "Active" and  subscription.expiry_date >= timezone.now():
                    return {"error": "User already has an active subscription."}

                if subscription.refund_id:
                    subscription.status = "Pending"
                    subscription.refund_id = None
                    subscription.save()

            # Step 2: Create PayPal subscription
            billing_plan = self._create_plan()  # Replace with actual plan ID
            start_time = (timezone.now()).isoformat(timespec="milliseconds") + "Z"


            subscription_data = {
                "name": "HTech Premium Monthly Subscription Plan",
                "description": "Subscription plan for users",
                "start_date": start_time,  # Static start time for testing
                "plan": {
                    "id":  billing_plan  # Replace with your PayPal Plan ID
                },
                "payer": {
                    "payment_method": "paypal"
                },

                  "override_merchant_preferences": {
                    "setup_fee": {"currency": "USD", "value": "2.00"},
                    "return_url": "http://localhost:8000/api/v1/subscription/paypal/execute/",
                    "cancel_url": "http://localhost:8000/api/v1/subscription/cancel-url/",
                    "auto_bill_amount": "YES",
                    "initial_fail_amount_action": "CONTINUE"}
                        
            }
            paypal_subscription = paypalrestsdk.BillingAgreement(subscription_data)
            if paypal_subscription.create():
                expiry_date = timezone.now() + timedelta(days=30)
                payment_token=self._extract_token(paypal_subscription.links[0].href)

                if subscription:
                    subscription.subscription_id = None
                    subscription.session_id='-'
                    subscription.payment_token=payment_token
                    subscription.start_date=timezone.now()
                    subscription.expiry_date = expiry_date
                    subscription.status = "Pending"
                    subscription.save()
                else:
                    Subscription.objects.create(
                        user=user,
                        plan_id=billing_plan,
                        session_id='-',
                        expiry_date=expiry_date,
                        payment_token=payment_token,
                        status="Pending"
                    )

               

                return {"subscription_id": paypal_subscription.id,"rel": paypal_subscription.links[0].rel,"checkout_url": paypal_subscription.links[0].href, "expiry_date": expiry_date}
            else:
                return {"error": f"Failed to create PayPal subscription: {paypal_subscription.error}"}
        except Exception as e:
            return {"error": str(e)}

    

    def cancel_subscription(self, user):
        """Cancel an active PayPal subscription and issue a refund."""
        try:
            subscription = Subscription.objects.filter(user=user, status="Active").first()
            if not subscription:
                return {"error": "No active subscription found."}

           
            start_date = (timezone.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = timezone.now().strftime("%Y-%m-%d")


            # Correct API call for transactions
            transactions = paypalrestsdk.api.default().get(
                f"/v1/payments/billing-agreements/{subscription.subscription_id}/transactions"
                f"?start_date={start_date}&end_date={end_date}"
            )

            profile=Profile.objects.filter(user=user).first()

            for transaction in transactions['agreement_transaction_list']:
                print(transaction['status'])
                if subscription.subscription_id==transaction['transaction_id'] and transaction['status']=='Created':
                    print(transaction)
                    # Create a refund
                    refund = paypalrestsdk.Payout({
                    "sender_batch_header": {
                        "sender_batch_id": "batch_" + str(timezone.now().timestamp()),
                        "email_subject": "You have received a payout!"
                    },
                    "items": [{
                        "recipient_type": "EMAIL",
                        "receiver":profile.paypal_payment_email ,
                        "amount": {
                            "value": "2.00",
                            "currency": "USD"
                        },
                        "note": "Thanks for your subscription refund",
                        "sender_item_id": "item_1"
                    }]
                })

                    if refund.create():
                                    # Find PayPal Billing Agreement
                        agreement = paypalrestsdk.BillingAgreement.find(subscription.subscription_id)

                        # Cancel the agreement
                        agreement.cancel({"note": "User requested cancellation."})

                        # Update subscription status in the database
                        subscription.status = "Cancelled"
                        subscription.expiry_date = timezone.now()
                        subscription.save()

                        return {"message": "Subscription canceled and refunded successfully."}

            return {"message": "Subscription canceled."}

        except paypalrestsdk.ResourceNotFound as e:
            return {"error": "Subscription not found on PayPal."}
        except Exception as e:
            return {"error": str(e)}

        
    def excute_subscription(self, request):
        token=request.GET.get("token")
        subscription = Subscription.objects.filter(payment_token=token).first()
        response=paypalrestsdk.BillingAgreement.execute(token)
        if response.success():
            if response.state=="Active":
                subscription.status="Active"
            subscription.subscription_id=response.id
            subscription.save()

        return {"message":"excuted"}