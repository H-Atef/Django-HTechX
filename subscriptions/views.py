from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.security.custom_jwt_auth import CustomJWTAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
import datetime
from subscriptions.models import Subscription
from subscriptions.helper import StripeClient,PayPalClient
import stripe

class CreateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]

    def post(self, request):
        response = StripeClient.create_subscription(request.user)
        if "error" in response:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response, status=status.HTTP_201_CREATED)

class ExecuteSubscriptionView(APIView):
    def get(self, request):
        session_id = request.GET.get("session_id")
        if not session_id:
            return Response({"error": "Missing session ID"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                subscription = Subscription.objects.get(session_id=session_id)
                subscription.status = "Active"
                subscription.subscription_id = session.get("subscription")
                subscription.start_date = datetime.datetime.now()
                subscription.save()
                return Response({"message": "Subscription activated successfully"}, status=status.HTTP_200_OK)
            return Response({"error": "Payment not completed"}, status=status.HTTP_400_BAD_REQUEST)
        except Subscription.DoesNotExist:
            return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)

class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomJWTAuthentication]

    def post(self, request):
        response = StripeClient.cancel_subscription(request.user)
        if "error" in response:
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response, status=status.HTTP_200_OK)
    
def stripe_subscription_cancel(request):
    """User cancels Stripe checkout before subscribing."""
    return Response({"message": "You canceled the approval process."}, status=status.HTTP_200_OK)
