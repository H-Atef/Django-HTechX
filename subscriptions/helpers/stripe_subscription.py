import stripe
from django.conf import settings
import datetime
from django.utils.timezone import timedelta
from subscriptions.models import Subscription
from subscriptions.helpers.base_subscription import BaseClient
from django.utils import timezone


stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeClient(BaseClient):
   
    def create_subscription(self,user):
        """Create Stripe checkout session with return URLs."""
        try:
            subscription = Subscription.objects.filter(user=user).first()

            if subscription:
                if subscription.status == "Active" and  subscription.expiry_date>= timezone.now():
                    return {"error": "User already has an active subscription."}

                if subscription.refund_id:
                    subscription.status = "Pending"
                    subscription.refund_id = None
                    subscription.save()

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price": "price_1QqgdUCc2StPaalT0ZmhguJd", "quantity": 1}],
                mode="subscription",
                success_url=f"http://localhost:8000/api/v1/subscription/stripe/execute/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"http://localhost:8000/api/v1/subscription/cancel-url/",
                customer_email=user.email
            )

            expiry_date = timezone.now() + timedelta(days=30)

            if subscription:
                subscription.subscription_id = None
                subscription.session_id = session.id
                subscription.expiry_date = expiry_date
                subscription.status = "Pending"
                subscription.save()
            else:
                Subscription.objects.create(
                    user=user,
                    subscription_id=None,
                    start_date=timezone.now(),
                    session_id=session.id,
                    plan_id="price_1QqgdUCc2StPaalT0ZmhguJd",
                    expiry_date=expiry_date,
                    status="Pending"
                )

            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "expiry_date": expiry_date
            }
        except stripe.error.StripeError as e:
            return {"error": str(e)}
        
    def excute_subscription(self, request):
            session_id = request.GET.get("session_id")
            if not session_id:
                return {"error": "Missing session ID"}

            try:
                session = stripe.checkout.Session.retrieve(session_id)
                if session.payment_status == "paid":
                    subscription = Subscription.objects.get(session_id=session_id)
                    subscription.subscription_id = session.get("subscription")
                    subscription.start_date = timezone.now()
                    subscription.save()
                    return {"message": "Subscription activated successfully"}
                return {"error": "Payment not completed"}
            except Subscription.DoesNotExist:
                return {"error": "Subscription not found."}


    def cancel_subscription(self,user):
        """Cancel an active subscription and issue a refund if applicable."""
        subscription = Subscription.objects.filter(user=user, status="Active").first()

        if not subscription:
            return {"error": "No active subscription found."}

        try:
            stripe.Subscription.modify(subscription.subscription_id, cancel_at_period_end=True)
            invoices = stripe.Invoice.list(subscription=subscription.subscription_id, limit=1)

            if not invoices.data:
                subscription.status = "Cancelled"
                subscription.expiry_date =timezone.now()
                subscription.save()
                return {"message": "Subscription canceled. No invoice found to refund."}

            latest_invoice = invoices.data[0]

            if latest_invoice.charge:
                refund = stripe.Refund.create(charge=latest_invoice.charge)
                subscription.status = "Cancelled"
                subscription.expiry_date = timezone.now()
                subscription.refund_id = refund.id
                subscription.save()
                return {"message": "Subscription canceled and refunded successfully."}

            subscription.status = "Cancelled"
            subscription.expiry_date = timezone.now()
            subscription.save()
            return {"message": "Subscription canceled but no charge found to refund."}

        except stripe.error.StripeError as e:
            return {"error": str(e)}


    
            
    def subscription_webhook(self, request):
        try:
            payload = request.body.decode("utf-8")
            sig_header = request.headers.get('Stripe-Signature',None)
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_SUBSCRIPTION_WEBHOOK_SECRET
            )
            
            data = event["data"]["object"]


    

            if event["type"] == "checkout.session.completed":
                session_id=data["id"]
                status=data["payment_status"]
                
                if status=="paid":
                    subscription = Subscription.objects.get(session_id=session_id)
                    subscription.start_date = timezone.now()
                    subscription.expiry_date = timezone.now() + timezone.timedelta(days=30) 
                    subscription.status = "Active"
                    subscription.save()
                    

          
            if event["type"] == "charge.refund.updated":
                refund_id=data['id']
                status=data['status']

                subscription = Subscription.objects.filter(refund_id=refund_id).first()


                if status=="succeeded":
                    subscription.start_date = timezone.now()
                    subscription.expiry_date = timezone.now() + timezone.timedelta(days=30)  # Adjust as needed
                    subscription.status = "Cancelled & Refunded"
                    subscription.save()



                   



            return {"status": "success", "message": "Webhook processed"}
    
        except stripe.error.SignatureVerificationError:
            return {"status": "error", "message": "Invalid signature"}
        except Exception as e:
            print(e)
            return {"status": "error", "message": str(e)}