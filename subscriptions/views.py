

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from subscriptions.helpers.subscription_context import SubscriptionContext
from users.security.custom_jwt_auth import CustomJWTAuthentication


class CreateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[CustomJWTAuthentication]

    def post(self, request, payment_method):
        context = SubscriptionContext(payment_method)
        context.initialize_payment_client()
        result = context.create_subscription(request.user)
        return Response(result)


class ExecuteSubscriptionView(APIView):
    def get(self, request, payment_method):
        context = SubscriptionContext(payment_method)
        context.initialize_payment_client()
        result = context.excute_subscription(request)
        return Response(result)


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes=[CustomJWTAuthentication]


    def post(self, request, payment_method):
        context = SubscriptionContext(payment_method)
        context.initialize_payment_client()
        result = context.cancel_subscription(request.user)
        return Response(result)

class SubscriptionWebhookView(APIView):
    """
    Handles webhooks to update payment statuses.
    """
    def post(self, request, payment_method):
        context = SubscriptionContext(payment_method)
        context.initialize_payment_client()
        response = context.subscription_webhook(request)
        return Response(response, status=200 if "error" not in response else 400)
    

class CancelView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        if request.GET.get('token'):
            return Response({"message": "Subscription cancellation page"}, status=200)
        return Response({"error": "Missing token"}, status=400)

