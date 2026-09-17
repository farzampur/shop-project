from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from core.models import Store
from core.views import StoreViewSet
from accounts.models import UserStore
from products.models import Category, Product, Supplier, Purchase
from sales.models import Customer, CustomerTransaction, Order
from products.views import CategoryViewSet, SupplierViewSet
from sales.views import CustomerViewSet


class Phase612DestructiveOperationIntegrityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.superuser = User.objects.create_superuser(
            username="phase612_admin", password="x"
        )
        self.manager = User.objects.create_user(
            username="phase612_manager", password="x"
        )
        self.store = Store.objects.create(name="Phase 6.12 Store", code="P612")
        UserStore.objects.create(
            user=self.manager, store=self.store, role="manager", is_active=True
        )

    def _delete(self, viewset, obj, user):
        request = self.factory.delete(f"/api/test/{obj.pk}/")
        force_authenticate(request, user=user)
        response = viewset.as_view({"delete": "destroy"})(request, pk=obj.pk)
        return response

    def test_store_with_business_history_cannot_be_deleted_even_without_userstore(self):
        UserStore.objects.filter(store=self.store).delete()
        Category.objects.create(name="Category", store=self.store)

        response = self._delete(StoreViewSet, self.store, self.superuser)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Store.objects.filter(pk=self.store.pk).exists())

    def test_clean_store_can_be_deleted_by_superuser(self):
        clean = Store.objects.create(name="Clean Store", code="P612-CLEAN")

        response = self._delete(StoreViewSet, clean, self.superuser)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Store.objects.filter(pk=clean.pk).exists())

    def test_category_with_product_cannot_be_deleted(self):
        category = Category.objects.create(name="Category", store=self.store)
        Product.objects.create(name="Product", barcode="P612-1", category=category)

        response = self._delete(CategoryViewSet, category, self.manager)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())

    def test_supplier_with_purchase_history_cannot_be_deleted(self):
        supplier = Supplier.objects.create(store=self.store, name="Supplier")
        Purchase.objects.create(
            supplier=supplier,
            store=self.store,
            user=self.manager,
        )

        response = self._delete(SupplierViewSet, supplier, self.manager)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Supplier.objects.filter(pk=supplier.pk).exists())

    def test_customer_with_financial_history_cannot_be_deleted(self):
        customer = Customer.objects.create(
            store=self.store,
            first_name="Customer",
            last_name="History",
            mobile="09120000001",
        )
        CustomerTransaction.objects.create(
            customer=customer,
            store=self.store,
            transaction_type="payment",
            amount="100",
        )

        response = self._delete(CustomerViewSet, customer, self.manager)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Customer.objects.filter(pk=customer.pk).exists())

    def test_customer_without_history_can_be_deleted(self):
        customer = Customer.objects.create(
            store=self.store,
            first_name="Clean",
            last_name="Customer",
            mobile="09120000002",
        )

        response = self._delete(CustomerViewSet, customer, self.manager)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Customer.objects.filter(pk=customer.pk).exists())
