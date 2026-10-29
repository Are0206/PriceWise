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

# SUPERMARKETS
supermarkets_json = client.get_supermarkets()
supermarkets = normalize_supermarkets(supermarkets_json) #supermarkets[i][{"api_id", "name"}]

#save
"""
for supermarket in supermarkets:
    #save
"""

# CATEGORIES PAGES PER SUPERMARKETS
for supermarket in supermarkets:
    id =
     