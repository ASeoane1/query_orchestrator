import psycopg

def startup(config):
    """
    :param config: config dict.
    """
    db_config = config.get("native_database")
    if not db_config:
        raise ValueError("Unable to find database connection values in the configuration file.")

    dbname = db_config.get("dbname")
    user = db_config.get("user")
    password = db_config.get("password")
    host = db_config.get("host", "localhost")
    port = db_config.get("port", 5432)

    try:
        conn = psycopg.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        print("✅ Connected succesfully.")

    except Exception as e:
        print(f"❌ Unnable to connect to database: {e}")
        raise


