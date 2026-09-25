# Pricing architecture

`Product` contains product identity/metadata only. It does not contain purchase or retail sale prices.

- Purchase cost and retail sale price are stored on `ProductBatch`.
- Retail selling price is the oldest sellable batch price (FIFO).
- Wholesale and special prices are stored in `ProductPrice`.
- `ProductPrice` retail records are not accepted by the API and are not used as a Product-level fallback.
- Sales require batch-controlled stock so the purchase cost snapshot is always auditable.
- Inventory value and potential profit reports are calculated from remaining batches.


## Legacy data migration

Migration `0027_remove_product_legacy_prices` preserves existing positive inventory that still has legacy Product prices by creating a synthetic opening Batch when no Batch already exists for that store. Legacy stock without a positive sale price is intentionally left unvalued rather than creating a zero-priced sellable Batch.
