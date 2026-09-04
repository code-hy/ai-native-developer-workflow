from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import FormView

from .forms import SignupForm


def _client_ip(request: HttpRequest) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


class SignupView(FormView):
    template_name = "accounts/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("households:create")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Account created. Create your household.")
        return super().form_valid(form)

    def get_success_url(self):
        token = self.request.session.get("pending_invite_token")
        if token:
            return f"/invite/{token}/"
        # respect ?next=
        nxt = self.request.GET.get("next") or self.request.POST.get("next")
        if nxt and nxt.startswith("/"):
            return nxt
        return str(self.success_url)


class RateLimitedLoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = False

    # 5 attempts per 60s per IP
    RATE_LIMIT = 5
    RATE_WINDOW = 60  # seconds

    @method_decorator(never_cache)
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        ip = _client_ip(request)
        key = f"login_attempts:{ip}"
        attempts = cache.get(key, 0)
        # If already rate limited on GET, show 429 immediately
        if request.method == "POST" and attempts >= self.RATE_LIMIT:
            return HttpResponse("Too Many Requests - rate limited", status=429)
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        # increment counter on failed login
        ip = _client_ip(self.request)
        key = f"login_attempts:{ip}"
        attempts = cache.get(key, 0)
        cache.set(key, attempts + 1, timeout=self.RATE_WINDOW)
        # generic error, don't leak email existence
        return super().form_invalid(form)

    def form_valid(self, form):
        # successful login resets counter
        ip = _client_ip(self.request)
        key = f"login_attempts:{ip}"
        cache.delete(key)
        return super().form_valid(form)

    def get_success_url(self):
        token = self.request.session.get("pending_invite_token")
        if token:
            return f"/invite/{token}/"
        return super().get_success_url()
