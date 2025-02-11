

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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


def subscription_cancel(request):
    return Response({"message": "Subscription cancellation page"})

