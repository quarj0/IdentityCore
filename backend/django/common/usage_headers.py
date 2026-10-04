class APIUsageHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        for key, value in getattr(request, "api_usage_headers", {}).items():
            response[key] = value
        if getattr(request, "api_usage_headers", None):
            response["Cache-Control"] = "no-store"
        return response
