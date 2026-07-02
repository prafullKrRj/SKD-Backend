"""Resolve the real client IP when running behind Cloudflare / Railway proxies.

DRF's throttle keys off ``request.META['REMOTE_ADDR']``. Behind a proxy that is
the proxy's IP, which would let every client share one throttle bucket. We
rewrite REMOTE_ADDR from the most trustworthy forwarded header available so
per-IP rate limits actually bind to the end user.
"""


class CloudflareRealIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        real_ip = self._client_ip(request)
        if real_ip:
            request.META["REMOTE_ADDR"] = real_ip
        return self.get_response(request)

    @staticmethod
    def _client_ip(request):
        # Cloudflare's dedicated header is the single original client IP.
        cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")
        if cf_ip:
            return cf_ip.strip()
        # Fall back to the left-most hop of X-Forwarded-For (the origin client).
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return None
