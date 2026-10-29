"""Orchestrates the Los Precios import, stage by stage.

Defines the order of the stages (supermarkets, catalog, prices), connects
the client, the normalizers and the loaders, and decides how to handle
partial failures so that one failing store does not abort the whole run.
Each stage can be executed on its own. Logs a summary at the end of each run.
"""
from client import LosPreciosClient
from normalizers import normalize_supermarkets, normalize_page
import os

CATEGORIES = [
    "Despensa",
    "Bebidas",
    "Frutas y Verduras",
    "Carnes y Pescados",
    "Panadería",
    "Comida Preparada",
    "Refrigerados",
    "Dulces y Pasabocas",
    "Cuidado Personal",
    "Aseo del Hogar",
    "Licores",
    "Bebés",
    "Mascotas",
    "Varios",
]

client = LosPreciosClient(api_key=os.environ['LOSPRECIOS_API_KEY'])

# IMPORT SUPERMARKETS
def import_supermarkets(client):
    supermarkets_json = client.get_supermarkets()
    supermarkets = normalize_supermarkets(supermarkets_json) #supermarkets[i][{"api_id", "name"}]

    #save
    """
    for supermarket in supermarkets:
        #save
    """


# IMPORT PRODUCTS PER CATEGORIES PAGES PER SUPERMARKETS
def import_products(client, supermarkets):
    for supermarket in supermarkets:
        id = supermarket["api_id"]
        
        if id == 6:
            continue #no products in exito
        
        for category in CATEGORIES:
            page_index = 1
            products_count = 0
            
            while True:
                page_json = client.get_supermarket_category_page(id=id, category=category, page=page_index)
                page = normalize_page(page_json) 
                
                if page_index == 1 and (page["total_items"] == 0 or page["total_items"] is None):
                    break #No products
                
                products = page["products"]
                #save products
                
                products_count += page["items_on_page"]  
                
                if page["items_on_page"] == 0 or products_count >= page["total_items"]:
                    break
                
                page_index += 1