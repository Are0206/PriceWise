from client import LosPreciosClient
from normalizers import normalize_supermarkets, normalize_page
import logging
import os

logger = logging.getLogger(__name__)

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

# Supermarket ID 6 has no products available.
SUPERMARKETS_WITHOUT_PRODUCTS = {6}


client = LosPreciosClient(api_key=os.environ['LOSPRECIOS_API_KEY'])

# IMPORT SUPERMARKETS
def import_supermarkets(client):
    supermarkets_json = client.get_supermarkets()
    supermarkets = normalize_supermarkets(supermarkets_json) #supermarkets[i][{"api_id", "name"}]

    """
    TODO: save in database
    for supermarket in supermarkets:
        #save
    """

    logger.info("Found %d supermarkets.", len(supermarkets))
    return supermarkets

#
                
