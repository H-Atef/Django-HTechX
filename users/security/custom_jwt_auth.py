from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger(__name__)

class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class that extends JWTAuthentication to:
    - Extract and validate the access token from the Authorization header.
    - Check if the access token is blacklisted.
    - Attach the user's role to the request object (optional).
    """
    def authenticate(self, request):
        try:
            # Retrieve access token from the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                # No access token provided, treat as anonymous user
                return (AnonymousUser(), None)

            # Extract the access token from the header
            access_token = auth_header.split(' ')[1]

            # Decode and validate the access token
            try:
                access_token = AccessToken(access_token)
                user = self.get_user(access_token)  # Get the user associated with the token
            except (InvalidToken, TokenError) as e:
                logger.error(f"Invalid access token: {e}")
                raise AuthenticationFailed('Invalid access token', code='invalid_token')


            # Return the user and token as per normal JWT authentication
            return user, access_token

        except AuthenticationFailed as auth_error:
            logger.error(f"Authentication failed: {auth_error}")
            return (AnonymousUser(), None)

        except Exception as e:
            logger.error(f"Unexpected error in authentication: {e}")
            return (AnonymousUser(), None)