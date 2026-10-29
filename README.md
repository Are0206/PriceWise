# PriceWise
 
A web application to compare product prices across supermarkets, build shopping lists, and find the cheapest place to buy them.
 
Course project — ST0251, Universidad EAFIT.
 
## Requirements
 
- Python 3.12 or newer
- Django 6.0

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
| `/products/favorite/toggle/<id>/` | Toggle product favorite status |
| `/products/<id>/review/` | Submit a product review |
| `/products/review/<id>/delete/` | Delete a product review |
| `/supermarkets/` | Supermarkets index list |
| `/supermarkets/<id>` | Supermarket details |
| `/supermarkets/<id>/review/` | Submit a supermarket review |
| `/supermarkets/review/<id>/delete/` | Delete a supermarket review |

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

### Accounts & Admin
| URL | Description |
|---|---|
| `/accounts/register/` | Register a new account |
| `/accounts/login/` | User login |
| `/accounts/logout/` | User logout |
| `/accounts/password/` | Change user password |
| `/admin/` | Administration panel |