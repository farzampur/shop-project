# ShopProject — Phase 6.9.4-H — CashBox Ledger Integrity

Baseline: Phase 6.9.4-G / `shopLast_6934_inventory_ledger_G_v3.zip`

## Changes

- Added `CashBoxTransaction.reference_type` to distinguish the business source of a ledger entry.
- CashBox balance cannot be changed through CashBox PATCH/PUT when `balance` is supplied.
- Registered CashBox transactions are immutable: PUT/PATCH/DELETE return 405.
- Generic CashBox transaction endpoint no longer accepts `receive` or `payment`; those entries must be created by the corresponding financial workflows.
- Manual `deposit` / `withdraw` remain available as explicit manual cashbox adjustments and are stored with `reference_type=manual` and no `reference_id`.
- Manual deposit/withdraw cannot carry an arbitrary `reference_id`.
- Existing financial workflows now tag their CashBox transactions:
  - sale / refund -> `order`
  - customer payment -> `customer_transaction`
  - expense -> `expense`
  - supplier payment -> `supplier_transaction`
  - cash transfer -> `cash_transfer`
- Added migration `sales/migrations/0018_cashboxtransaction_reference_type.py`.
- Added `sales/test_phase6_9_4_h.py` with six focused integrity tests.

## Verification

The container used for packaging does not have the project's Django environment installed (`ModuleNotFoundError: django`), so the Django test suite was NOT executed here.

`python -m compileall` completed successfully for the prepared backend source.

Run the focused test on the user's existing `(venv)` first, then the full suite.
