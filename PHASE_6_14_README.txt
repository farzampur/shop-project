Phase 6.14 — API Validation & State Transition Integrity

Base: current main at ac7399cb898595007a4f8941a050a89544ed4e37

Scope
- Prevent mutation of received purchases through generic update.
- Prevent injecting received=True through generic purchase update.
- Prevent changing purchase store during update.
- Prevent destructive purchase cleanup from deleting an unrelated supplier-ledger row with a colliding reference_id.
- Prevent purchase returns for products belonging to another store.
- Verify invalid return operations leave inventory/ledger state unchanged.
- Verify purchase returns are immutable after creation.
- Verify client-supplied return unit_price cannot override the purchase-item price.

Changed production files
- backend/products/views.py
- backend/products/serializers.py

New targeted tests
- backend/products/test_phase6_14.py

Run only the Phase 6.14 tests first:
python manage.py test products.test_phase6_14

Expected result:
Ran 8 tests ... OK

Do not run the full suite for this phase unless a targeted test exposes a regression that requires broader verification.
