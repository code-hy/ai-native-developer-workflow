from django.contrib import admin

from .models import Household, Invite, Membership


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "timezone", "created_by", "created_at"]
    list_filter = ["type"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "household", "role", "joined_at"]
    list_filter = ["role"]


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ["email", "household", "role", "token", "expires_at", "accepted_at"]
    readonly_fields = ["token"]
