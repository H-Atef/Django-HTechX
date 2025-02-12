from django.urls import path
from .views import (
    CreateSubscriptionView, ExecuteSubscriptionView, 
    CancelSubscriptionView,SubscriptionWebhookView ,CancelView
)

urlpatterns = [
    path("<str:payment_method>/create/", CreateSubscriptionView.as_view(), name="create_subscription"),
    path("<str:payment_method>/execute/", ExecuteSubscriptionView.as_view(), name="execute_subscription"),
    path("<str:payment_method>/cancel/", CancelSubscriptionView.as_view(), name="cancel_subscription"),
    path("<str:payment_method>/webhook/",SubscriptionWebhookView.as_view(),name="subscription_webhook"),
    path("cancel-url/", CancelView.as_view(), name="subscription_cancel"),
]
