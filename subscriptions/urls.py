from django.urls import path
from .views import (
    CreateSubscriptionView, ExecuteSubscriptionView, 
    CancelSubscriptionView, subscription_cancel
)

urlpatterns = [
    path("<str:payment_method>/create/", CreateSubscriptionView.as_view(), name="create_subscription"),
    path("<str:payment_method>/execute/", ExecuteSubscriptionView.as_view(), name="execute_subscription"),
    path("<str:payment_method>/cancel/", CancelSubscriptionView.as_view(), name="cancel_subscription"),
    path("cancel-url/", subscription_cancel, name="subscription_cancel"),
]
