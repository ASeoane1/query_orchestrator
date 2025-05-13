
import psycopg2
from psycopg2 import extras


START_SEQUENCE = 'sql/native/remake.sql'

class PostgresqlUtils:
    def __init__(self, config):
        """
        """
        self.config = config
        if not config:
            raise ValueError("❌ Unable to find database connection values in the configuration file.")

        dbname = config.get("dbname")
        user = config.get("user")
        password = config.get("password")
        host = config.get("host", "localhost")
        port = config.get("port", 5432)
        self.open_connection(dbname, user, password, host, port)

    def open_connection(self, dbname, user, password, host, port):
        try:
            self.connection = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            self.connection.autocommit = True
            print("✅ Connected successfully to {} database.".format(dbname))
        except Exception as e:
            print("❌ Unable to connect to {} database: {e}".format(dbname))
            raise
    
    def close_connection(self):
        self.connection.close()

    def clean_database(self):
        """
        Drops and recreates the schema 'query_orchestrator' along with its tables.
        :param conn: Active psycopg connection to PostgreSQL.
        """
        try:
            with open(START_SEQUENCE, "r", encoding="utf-8") as f:
                script = f.read()
            print("🔄 Cleaning database: Rebuilding native structure...")
            queries = script.split(";")
            cur = self.connection.cursor()
            for query in queries:
                query = query.strip()
                if query:
                    cur.execute(query)

            print("✅ Database cleaned and schema recreated successfully.")

            self.close_connection()
        
        except Exception as e:
            print(f"❌ Error while cleaning database: {e}")
            raise

    def execute_query_with_return(self, query):
        """
        Executes a query for postgresql
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except Exception as e:
            print(f"❌ Error while executing query: {e}")
            return None
        
    def execute_query_with_dict_return(self, query):
        try:
            with self.connection.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return result
        except Exception as e:
            print(f"❌ Error while executing query: {e}")
            return None
        
    def execute_query_without_return(self, query):
        """
        Executes a query for postgresql
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
        except Exception as e:
            print(f"❌ Error while executing query: {e}")
            return None
        
    def insert_rollback(self, query, rollback):
        """
        Inserts rollback
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("INSERT INTO query_orchestrator.history (\"query\", \"rollback\") VALUES (%s, %s) RETURNING id",(query, rollback))
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"❌ Error while executing query: {e}")
            return None
        
    def load_query(self, file_name, schema = '', table = ''):
        with open(file_name, 'r', encoding='utf-8') as file:
            query = file.read()
        query = query.replace('{$schema}', schema).replace('{$table}', table)
        return query