import psycopg

def startup(config):
    """
    Initializes a connection to the PostgreSQL database.

    :param config: Dictionary containing the database configuration.
    :return: psycopg connection object.
    """
    db_config = config.get("native_database")
    if not db_config:
        raise ValueError("❌ Unable to find database connection values in the configuration file.")

    dbname = db_config.get("dbname")
    user = db_config.get("user")
    password = db_config.get("password")
    host = db_config.get("host", "localhost")
    port = db_config.get("port", 5432)

    try:
        # Establish connection
        conn = psycopg.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            autocommit=True
        )
        print("✅ Connected successfully to the database.")

        # Clean and initialize the database
        _clean_database(conn)

    except Exception as e:
        print(f"❌ Unable to connect to database: {e}")
        raise

def _clean_database(conn):
    """
    Drops and recreates the schema 'query_orchestrator' along with its tables.
    :param conn: Active psycopg connection to PostgreSQL.
    """
    try:
        with conn.cursor() as cur:
            print("🔄 Cleaning database: Dropping schema and recreating tables...")

            # Drop schema and cascade all objects
            cur.execute("DROP SCHEMA IF EXISTS query_orchestrator CASCADE;")

            # Recreate schema
            cur.execute("CREATE SCHEMA IF NOT EXISTS query_orchestrator;")

            # Create tables
            cur.execute("""
                CREATE TABLE IF NOT EXISTS query_orchestrator.schemas (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    "group" TEXT NOT NULL
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS query_orchestrator.tables (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    "schema" INT NOT NULL,
                    CONSTRAINT fk_schema FOREIGN KEY ("schema") 
                        REFERENCES query_orchestrator.schemas(id) 
                        ON DELETE CASCADE
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS query_orchestrator.constraints (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    origin_table INT NOT NULL,
                    destination_table INT NOT NULL,
                    origin_key TEXT NOT NULL,
                    destination_key TEXT NOT NULL,
                    CONSTRAINT fk_origin_table FOREIGN KEY (origin_table) 
                        REFERENCES query_orchestrator.tables(id) 
                        ON DELETE CASCADE,
                    CONSTRAINT fk_destination_table FOREIGN KEY (destination_table) 
                        REFERENCES query_orchestrator.tables(id) 
                        ON DELETE CASCADE
                );
            """)

            print("✅ Database cleaned and schema recreated successfully.")
    
    except Exception as e:
        print(f"❌ Error while cleaning database: {e}")
        raise
