from ipaddress import ip_address, ip_network

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.api_clients.models import APIClient, APIClientStatus


class APIClientAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        client_id = request.headers.get("X-Client-Id")
        authorization = request.headers.get("Authorization", "")

        if not client_id and not authorization:
            return None
        if not client_id or not authorization.startswith(f"{self.keyword} "):
            raise AuthenticationFailed("Missing API client credentials.")

        raw_secret = authorization[len(self.keyword) + 1 :].strip()
        try:
            api_client = APIClient.objects.select_related("tenant").get(client_id=client_id)
        except APIClient.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid API client credentials.") from exc

        if api_client.status != APIClientStatus.ACTIVE:
            raise AuthenticationFailed("API client is not active.")
        if not api_client.verify_client_secret(raw_secret):
            raise AuthenticationFailed("Invalid API client credentials.")
        if api_client.allowed_ips and not self._is_request_ip_allowed(request, api_client.allowed_ips):
            raise AuthenticationFailed("Request IP is not allowed for this API client.")

        api_client.last_used_at = timezone.now()
        api_client.save(update_fields=["last_used_at", "updated_at"])
        request.api_client = api_client
        request.tenant = api_client.tenant
        return (api_client, raw_secret)

    def _is_request_ip_allowed(self, request, allowed_networks: list[str]) -> bool:
        remote_addr = request.META.get("REMOTE_ADDR")
        if not remote_addr:
            return False

        address = ip_address(remote_addr)
        return any(address in ip_network(network, strict=False) for network in allowed_networks)
