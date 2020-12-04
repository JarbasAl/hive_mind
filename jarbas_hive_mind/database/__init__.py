from jarbas_hive_mind.configuration import CONFIGURATION, default_config
from ovos_utils.log import LOG


if "sql" not in CONFIGURATION["database"].split(":/")[0]:
    from jarbas_hive_mind.database.json_db import JsonClientDatabase
    ClientDatabase = JsonClientDatabase
else:
    try:
        from jarbas_hive_mind.database.sql import SQLClientDatabase
        ClientDatabase = SQLClientDatabase
    except ImportError:
        LOG.error("Run pip install sqlalchemy")

        LOG.info("Falling back to json database")
        CONFIGURATION["database"] = default_config()["database"]
        CONFIGURATION.store()
        from jarbas_hive_mind.database.json_db import JsonClientDatabase

        ClientDatabase = JsonClientDatabase

