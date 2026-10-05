"""Cache wrapped key records only for the duration of one HTTP request."""

from common.tenant_crypto import read_key_records


class TenantKeyReadCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = read_key_records.set({})
        try:
            return self.get_response(request)
        finally:
            read_key_records.reset(token)
