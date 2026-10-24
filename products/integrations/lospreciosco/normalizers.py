"""Converts raw Los Precios API payloads into clean dictionaries.

This is the only module that knows the API's response format (accented
keys, inconsistent key names, nested price lists). If the API changes,
only this file should need updating. Also contains the EAN-8 to EAN-13
conversion helper described in the API documentation.

Does not import Django and does not perform any network or database access.
"""