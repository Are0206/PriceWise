# PriceWise
 
A web application to compare product prices across supermarkets, build shopping lists, and find the cheapest place to buy them.
 
Course project — ST0251, Universidad EAFIT.
 
## Requirements
 
- Python 3.12 or newer (CI runs 3.14)
- The packages in `requirements.txt` (Django 6.0.8, Pillow 13, requests)

## Setup
 
Clone the repository and enter the project folder:
 
```bash
git clone https://github.com/Are0206/PriceWise.git
cd PriceWise
```
 
Install the required dependencies from the requirements file (do not install libraries directly):
 
```bash
pip install -r requirements.txt
```
 
Ensure your database is up to date with the latest migrations:
 
```bash
python manage.py migrate
```
 
Create an administrator account. **This superuser account is required to log into the Django admin panel, where you can manage, add, edit, or delete products, supermarkets, categories, and prices.** You will be asked for a username and password:
 
```bash
python manage.py createsuperuser
```
 
## Running the project
 
```bash
python manage.py runserver
```
 
The application will be available at http://127.0.0.1:8000/

## Configuration

Settings come from environment variables or from the `.env` file in the project root. With nothing set, the project runs in development mode, so no setup is needed to work locally.

| Variable | Default | Meaning |
|---|---|---|
| `DJANGO_ENV` | `development` | `development` or `production`. Production validates the rest and refuses to start if something is unsafe. |
| `DJANGO_DEBUG` | `true` in development | Must be set to `false` in production. Accepts `true/false`, `1/0`, `yes/no`, `on/off`. |
| `DJANGO_SECRET_KEY` | development key | Required in production: at least 50 characters, not a `django-insecure` key. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | Comma-separated hosts. Required in production, no `*`. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Comma-separated origins, e.g. `https://pricewise.example.com`. |
| `DJANGO_SECURE_SSL_REDIRECT` | `true` in production | Redirect HTTP to HTTPS. |
| `DJANGO_SECURE_HSTS_SECONDS` | `3600` in production | Raise it once HTTPS works on every host. |
| `DJANGO_TRUST_PROXY_SSL` | `false` | Set to `true` only behind a reverse proxy that sets `X-Forwarded-Proto`. |
| `DJANGO_LOG_LEVEL` | `INFO` | Level of the `products` logger (the Los Precios import summary). |
| `LOSPRECIOS_API_KEY` | none | Key for the Los Precios import. |

Generate a production secret key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Tests

```bash
python manage.py test
```

GitHub Actions runs the tests and a missing-migrations check on every push and pull request to `main` and `develop`.
 
## Database and Data
 
The database is included in the repository, so it already contains the necessary information about products, supermarkets, and categories to use the app right away.

To modify this data, add new products, or update prices, sign in to the admin panel at http://127.0.0.1:8000/admin/ using the superuser account you created earlier.
 
## Importing data from Los Precios

Products, prices and supermarkets can be imported from the [Los Precios](https://losprecios.co) API.

1. Create a file named `.env` in the project root (next to `manage.py`) with the API key:

   ```
   LOSPRECIOS_API_KEY=your-key
   ```

   `.env` is in `.gitignore`: never commit the key or paste it in code, issues or the wiki.

2. Run the import:

   ```bash
   python manage.py sync_losprecios
   ```

   Useful options: `--store 1` (only one store, by its API id), `--category Despensa` (only one category), `--max-pages 2` (quick test), `--only-supermarkets`. `--store` and `--category` can be repeated.

Running it again updates the same products instead of duplicating them. Products get the category they have on Los Precios. Each time a price changes, a dated row is added to the price history, so run the import once a day to build up the history. The API allows one request per second, so a full import takes around 20 minutes.

3. Once the real data is in, remove the hand-made demo catalog (products and supermarkets without an API id):

   ```bash
   python manage.py remove_demo_data        # shows what would be deleted
   python manage.py remove_demo_data --yes  # deletes it
   ```

## Main URLs
 
### Products & Supermarkets
| URL | Description |
|---|---|
| `/` | Home page with product search |
| `/products/<id>/` | Product details |
| `/products/<id>/compare/` | Price comparison across supermarkets |
| `/products/favorites/` | The user's favorite products |
| `/products/favorite/toggle/<id>/` | Toggle product favorite status |
| `/products/<id>/review/` | Submit a product review |
| `/products/review/<id>/delete/` | Delete a product review |
| `/products/supermarkets/` | Supermarkets index list |
| `/products/supermarkets/<id>` | Supermarket details |
| `/products/supermarkets/<id>/review/` | Submit a supermarket review |
| `/products/supermarkets/review/<id>/delete/` | Delete a supermarket review |

### Shopping Lists
| URL | Description |
|---|---|
| `/lists/` | All shopping lists |
| `/lists/create/` | Create a new shopping list |
| `/lists/<uuid>/` | Shopping list details, with cheapest supermarket and estimated savings |
| `/lists/<uuid>/edit/` | Edit a shopping list |
| `/lists/<uuid>/delete/` | Delete a shopping list |
| `/lists/<uuid>/share/` | Share a shopping list |
| `/lists/<uuid>/duplicate/` | Duplicate a shopping list |
| `/lists/<uuid>/add/` | Add one product to a list (from a product card) |

### Accounts & Admin
| URL | Description |
|---|---|
| `/accounts/register/` | Register a new account |
| `/accounts/login/` | User login |
| `/accounts/logout/` | User logout |
| `/accounts/password/` | Change user password |
| `/admin/` | Administration panel |