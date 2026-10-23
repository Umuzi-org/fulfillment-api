# Inventory and Supply Chain Fulfilment API

JSON API for warehouses, products, stock movements, accounts, and fulfillment orders.

The interactive reference is the Swagger UI at [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) once the API is running. The OpenAPI document is at [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/).

## Setup

From this directory:

```bash
docker compose up
```

That starts PostgreSQL and the API. The API waits until the database accepts connections, applies migrations, and listens on port 8000. The local database name, user, and password are `fulfilment`.

Create the first admin. Further accounts are created through the API.

```bash
docker compose exec web python manage.py createsuperuser
```

The prompt asks for an email and a password. `GET http://localhost:8000/health/` returns `{"status": "ok", "database": "ok", ...}` when the service and the database are up.

## Requests

Replace the email and password with the admin you just created. The login response includes `access`. Send that value as `Authorization: Bearer <access>` on the calls below.

```bash
curl -s -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your-password"}'
```

Warehouses. An admin creates one. Any signed-in user can list them.

```bash
curl -s -X POST http://localhost:8000/api/warehouses/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Main", "location": "Dock 1", "capacity": 100}'
```

Products. `warehouses` is a list of warehouse ids. The server owns `stock_quantity`.

```bash
curl -s -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"sku": "CRATE-1", "name": "Crate", "unit_price": "12.50", "warehouses": [1]}'
```

Stock movements. `IN` adds to the product quantity and `OUT` subtracts from it. The account is the signed-in admin.

```bash
curl -s -X POST http://localhost:8000/api/stock-movements/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"product": 1, "warehouse": 1, "direction": "IN", "quantity": 10}'
```

Accounts. An admin creates the next account. The password is write-only.

```bash
curl -s -X POST http://localhost:8000/api/accounts/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"email": "ada@example.com", "password": "correct-horse-battery", "role": "STANDARD"}'
```

Orders. The account is the signed-in user. Each line's price is copied from the product. The client does not send `unit_price`.

```bash
curl -s -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"lines": [{"product": 1, "quantity": 2}]}'
```

Use the ids from the create responses in place of `1`.

## Indexes

These indexes match the lookups the API makes.

| Index | Columns | Why it is there |
| --- | --- | --- |
| Unique on `Account.email` | `email` | Login and account lookup use the email, and two accounts cannot share one. |
| Unique on `Product.sku` | `sku` | A product is identified by its stock code, and that code is used when a product is created. |
| `product_is_active_idx` | `Product.is_active` | The catalogue for a standard user is the set of active products. |
| `order_account_status_idx` | `FulfillmentOrder.account`, `status` | A person's order list is filtered by owner, and cancellation depends on the order still being `PENDING`. |
| `order_created_at_idx` | `FulfillmentOrder.created_at` | Order lists are ordered by when the order was placed. |
| `movement_product_created_idx` | `StockMovement.product`, `created_at` | A product's stock history is read for that product, in time order. |
