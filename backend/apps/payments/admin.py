from django.contrib import admin

from .models import SubscriptionPlan, UserSubscription

# Both admins exist mainly so a developer/admin can inspect these tables
# during Phase 1 (they hold zero real rows until Phase 2 Stripe activation)
# — not meant as a content-editing workflow the way the questions/taxonomy
# admins are.


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "interval", "trial_period_days", "trial_question_limit", "stripe_price_id")


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "current_period_end")
    list_filter = ("status", "plan")
    search_fields = ("user__email",)
