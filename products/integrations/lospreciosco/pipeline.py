"""Orchestrates the Los Precios import, stage by stage.

Defines the order of the stages (supermarkets, catalog, prices), connects
the client, the normalizers and the loaders, and decides how to handle
partial failures so that one failing store does not abort the whole run.
Each stage can be executed on its own. Logs a summary at the end of each run.
"""