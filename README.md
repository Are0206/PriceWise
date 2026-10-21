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