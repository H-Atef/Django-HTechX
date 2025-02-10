from django.urls import path
from .views import (
    CreateSubscriptionView, ExecuteSubscriptionView, 
    CancelSubscriptionView, stripe_subscription_cancel
)

urlpatterns = [
    path("create/", CreateSubscriptionView.as_view(), name="create_subscription"),
    path("execute/", ExecuteSubscriptionView.as_view(), name="execute_subscription"),
    path("cancel/", CancelSubscriptionView.as_view(), name="cancel_subscription"),
    path("cancel-url/", stripe_subscription_cancel, name="stripe_subscription_cancel"),
]
