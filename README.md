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
 
Install Django:
 
```bash
pip install django
```
 
Create the database:
 
```bash
python manage.py migrate
```
 
Create an administrator account (you will be asked for a username and password):
 
```bash
python manage.py createsuperuser
```
 
## Running the project
 
```bash
python manage.py runserver
```
 
The application will be available at http://127.0.0.1:8000/
 
## Loading data
 
The database starts empty, so there is nothing to compare yet. Sign in to the admin
panel at http://127.0.0.1:8000/admin/ with the superuser account and register, in this order:
 
1. **Supermarkets** — at least two, so comparisons have something to compare.
2. **Products** — name, description, and image.
3. **Prices** — one price per product per supermarket.
Once there is data, the rest of the site works.
 
## Main URLs
 
| URL | Description |
|---|---|
| `/` | Home page with product search |
| `/products/<id>/` | Product details |
| `/products/<id>/compare/` | Price comparison across supermarkets |
| `/lists/` | All shopping lists |
| `/lists/create/` | Create a shopping list |
| `/lists/<id>/` | Shopping list details, with cheapest supermarket and estimated savings |
| `/lists/<id>/edit/` | Edit a shopping list |
| `/admin/` | Administration panel |
