from django.core.management.base import BaseCommand, CommandError

from core.models import Store
from accounting.services import ensure_store_setup, sync_store


class Command(BaseCommand):
    help = "همگام‌سازی idempotent سوابق مالی فعلی با دفتر حسابداری مستقل"

    def add_arguments(self, parser):
        parser.add_argument("--store", type=int, help="شناسه یک فروشگاه")

    def handle(self, *args, **options):
        store_id = options.get("store")
        stores = Store.objects.filter(is_active=True)
        if store_id:
            stores = stores.filter(pk=store_id)
            if not stores.exists():
                raise CommandError("فروشگاه پیدا نشد.")
        count = 0
        for store in stores.order_by("id"):
            ensure_store_setup(store)
            sync_store(store)
            count += 1
            self.stdout.write(self.style.SUCCESS(f"حسابداری فروشگاه {store.name} همگام شد."))
        self.stdout.write(self.style.SUCCESS(f"تعداد فروشگاه‌های همگام‌شده: {count}"))
