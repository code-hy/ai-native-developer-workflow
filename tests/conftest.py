import pytest

# --- Python 3.14 compatibility patch for Django template context ---
# Django <5.2's BaseContext.__copy__ uses copy(super()) which fails on Python 3.14
# https://code.djangoproject.com/ticket/36000, fixed in Django 5.2
try:
    from django.template.context import BaseContext, RequestContext

    def _fixed_copy(self):
        # Replicate BaseContext.__copy__ without copy(super())
        # super() returns a super object which copy() cannot handle on Python 3.14
        dup = self.__class__.__new__(self.__class__)
        dup.__dict__.update(self.__dict__)
        # shallow copy dicts list
        try:
            dup.dicts = self.dicts[:]
        except AttributeError:
            pass
        return dup

    # Patch both BaseContext and RequestContext (__copy__ inherited)
    BaseContext.__copy__ = _fixed_copy  # type: ignore[attr-defined]
    # RequestContext may have its own __copy__; ensure it's patched too
    if hasattr(RequestContext, "__copy__"):
        RequestContext.__copy__ = _fixed_copy  # type: ignore[attr-defined]
except Exception:
    pass


@pytest.fixture
def household(db):
    from households.models import Household  # noqa: F401 — placeholder until real model

    pytest.skip("household model not yet implemented — scaffold")
