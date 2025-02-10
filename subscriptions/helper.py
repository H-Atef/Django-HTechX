import stripe
from django.conf import settings
import datetime
from django.utils.timezone import timedelta
from subscriptions.models import Subscription
import paypalrestsdk

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeClient:
    @staticmethod
    def create_subscription(user):
        """Create Stripe checkout session with return URLs."""
        try:
            subscription = Subscription.objects.filter(user=user).first()

            if subscription:
                if subscription.status == "Active" and  subscription.expiry_date and subscription.expiry_date.timestamp() >= datetime.datetime.now().timestamp():
                    return {"error": "User already has an active subscription."}

                if subscription.refund_id:
                    subscription.status = "Pending"
                    subscription.refund_id = None
                    subscription.save()

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price": "price_1QqgdUCc2StPaalT0ZmhguJd", "quantity": 1}],
                mode="subscription",
                success_url=f"http://localhost:8000/api/v1/subscription/execute/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"http://localhost:8000/api/v1/subscription/cancel-url/",
                customer_email=user.email
            )

            expiry_date = datetime.datetime.now() + timedelta(days=30)

            if subscription:
                subscription.subscription_id = session.subscription
                subscription.session_id = session.id
                subscription.expiry_date = expiry_date
                subscription.status = "Pending"
                subscription.save()
            else:
                Subscription.objects.create(
                    user=user,
                    subscription_id=session.subscription,
                    session_id=session.id,
                    plan_id="price_1QqgdUCc2StPaalT0ZmhguJd",
                    expiry_date=expiry_date,
                    status="Pending"
                )

            return {
                "session_id": session.id,
                "subscription_id": session.subscription,
                "checkout_url": session.url,
                "expiry_date": expiry_date
            }
        except stripe.error.StripeError as e:
            return {"error": str(e)}

    @staticmethod
    def cancel_subscription(user):
        """Cancel an active subscription and issue a refund if applicable."""
        subscription = Subscription.objects.filter(user=user, status="Active").first()

        if not subscription:
            return {"error": "No active subscription found."}

        try:
            stripe.Subscription.modify(subscription.subscription_id, cancel_at_period_end=True)
            invoices = stripe.Invoice.list(subscription=subscription.subscription_id, limit=1)

            if not invoices.data:
                subscription.status = "Cancelled"
                subscription.expiry_date = datetime.datetime.now()
                subscription.save()
                return {"message": "Subscription canceled. No invoice found to refund."}

            latest_invoice = invoices.data[0]

            if latest_invoice.charge:
                refund = stripe.Refund.create(charge=latest_invoice.charge)
                subscription.status = "Cancelled"
                subscription.expiry_date = datetime.datetime.now()
                subscription.refund_id = refund.id
                subscription.save()
                return {"message": "Subscription canceled and refunded successfully."}

            subscription.status = "Cancelled"
            subscription.expiry_date = datetime.datetime.now()
            subscription.save()
            return {"message": "Subscription canceled but no charge found to refund."}

        except stripe.error.StripeError as e:
            return {"error": str(e)}



paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" in production
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})

class PayPalClient:
    @staticmethod
    def get_existing_plan():
        """Retrieve an existing PayPal subscription plan."""
        try:
            plans = paypalrestsdk.BillingPlan.all({"status": "ACTIVE"})
            if plans and len(plans["plans"]) > 0:
                return plans["plans"][0]["id"]  
        except Exception as e:
            return None 
        return None

    @staticmethod
    def create_plan():
        """Create a PayPal subscription plan if not already created."""
        try:
            # Step 1: Check if an active plan already exists
            existing_plan_id = PayPalClient.get_existing_plan()
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
                    "return_url": "http://localhost:8000/api/v1/subscription/execute/",
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
        
    @staticmethod
    def create_subscription(user):
        """Create PayPal subscription checkout session."""
        try:
            # Step 1: Check if user already has an active or refunded subscription
            subscription = Subscription.objects.filter(user=user).first()

            if subscription:
                if subscription.status == "Active" and  subscription.expiry_date and subscription.expiry_date.timestamp() >= datetime.datetime.now().timestamp():
                    return {"error": "User already has an active subscription."}

                if subscription.refund_id:
                    subscription.status = "Pending"
                    subscription.refund_id = None
                    subscription.save()

            # Step 2: Create PayPal subscription
            billing_plan = PayPalClient.create_plan()  # Replace with actual plan ID
            start_time = (datetime.datetime.now()).isoformat(timespec="milliseconds") + "Z"


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

                 "merchant_preferences": {
                    "return_url": "http://localhost:8000/api/v1/subscription/execute/",
                    "cancel_url": "http://localhost:8000/api/v1/subscription/cancel-url/",
                
                }
            }
            paypal_subscription = paypalrestsdk.BillingAgreement(subscription_data)
            if paypal_subscription.create():
                expiry_date = datetime.datetime.now() + timedelta(days=30)

                if subscription:
                    subscription.subscription_id = None
                    subscription.start_date=datetime.datetime.now()
                    subscription.expiry_date = expiry_date
                    subscription.status = "Pending"
                    subscription.save()
                else:
                    Subscription.objects.create(
                        user=user,
                        plan_id=billing_plan,
                        expiry_date=expiry_date,
                        status="Pending"
                    )

                return {"subscription_id": paypal_subscription.id,"rel": paypal_subscription.links[0].rel,"checkout_url": paypal_subscription.links[0].href, "expiry_date": expiry_date}
            else:
                return {"error": f"Failed to create PayPal subscription: {paypal_subscription.error}"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def cancel_subscription(user):
        """Cancel an active PayPal subscription and issue a refund."""
        try:
            subscription = Subscription.objects.filter(user=user, status="Active").first()
            if not subscription:
                return {"error": "No active subscription found."}

            agreement = paypalrestsdk.BillingAgreement.find(subscription.subscription_id)
            agreement.cancel({"note": "User requested cancellation."})

            subscription.status = "Cancelled"
            subscription.expiry_date = datetime.datetime.now()
            subscription.save()

            # Process refund
            transactions = agreement.transactions()
            if transactions and transactions["transactions"]:
                sale_id = transactions["transactions"][0]["related_resources"][0]["sale"]["id"]
                refund = paypalrestsdk.Refund({"amount": {"total": "10.00", "currency": "USD"}})
                refund.sale_id = sale_id
                if refund.create():
                    subscription.refund_id = refund.id
                    subscription.save()
                    return {"message": "Subscription canceled and refunded successfully."}
                return {"message": "Subscription canceled but refund failed."}

            return {"message": "Subscription canceled."}
        except Exception as e:
            return {"error": str(e)}