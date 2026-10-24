"""Writes normalized Los Precios data into the Django models.

The only module (together with the pipeline) that touches the database.
Performs idempotent upserts of supermarkets, categories, products and
current prices, and inserts a PriceHistory row only when the amount or the
price date changes. Price updates and their history are written inside a
single transaction to keep both in sync.
"""