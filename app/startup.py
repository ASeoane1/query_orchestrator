import psycopg
from .postgresql_utils import PostgresqlUtils
from .postgre_rollback_generator import PostgreRollbackGenerator

TABLE_NAMES_QUERY = 'sql/autopopulate/table_names.sql'
TABLE_ID_QUERY = 'sql/autopopulate/table_id.sql'
TABLE_CONSTRAINTS_QUERY = 'sql/autopopulate/table_constraints.sql'

class Startup:
    def __init__(self, config):
        self.config = config
        db_config = self.config.get("native_database")
        self.postgresql_utils = PostgresqlUtils(db_config)

    def run(self):
        """
        Cleans and populates database
        """
        try:
            self.postgresql_utils.clean_database()
            self.populate_database()
        except Exception as e:
            print(f"❌ Error during startup: {e}")
            raise

    def populate_database(self):
        """
        Populates database
        """

        postgre_rollback_generator = PostgreRollbackGenerator(self.postgresql_utils)


        groups = self.config.get("groups", [])
        for group in groups:
            #Open connection for the current group
            self.postgresql_utils.open_connection(dbname=group[0].get("dbname"),user=group[0].get("user"), password=group[0].get("password"), host=group[0].get("host"),port=group[0].get("port"))
            print("🔄 Loading schema: {}".format(group[0].get("schema")))
            #Insert current group schema
            query = "INSERT INTO query_orchestrator.schemas (name, \"group\") VALUES ('{}', '{}');".format(group[0].get("schema"), group[0].get("name"))
            self.postgresql_utils.execute_query_without_return(query)

            #Get current group tables
            query = "SELECT * FROM query_orchestrator.schemas WHERE name = '{}' AND \"group\" = '{}'".format(group[0].get("schema"), group[0].get("name"))
            schema = self.postgresql_utils.execute_query_with_return(query)
            query = self.postgresql_utils.load_query(file_name=TABLE_NAMES_QUERY,schema=group[0].get("schema"))

            tables = self.postgresql_utils.execute_query_with_return(query)

            #Loop current group tables
            print("🔄 Loading {} tables...".format(group[0].get("schema")))
            for table in tables:
                #Get current table id
                query = self.postgresql_utils.load_query(file_name=TABLE_ID_QUERY,schema=group[0].get("schema"),table=table[0])
                table_id = self.postgresql_utils.execute_query_with_return(query)
                #Insert current group tables
                query = "INSERT INTO query_orchestrator.tables (name, schema, table_id, serial_id) VALUES ('{}', '{}', '{}', '{}');".format(table[0], schema[0][0], table_id[0][0], table_id[0][1])
                self.postgresql_utils.execute_query_without_return(query)
            print("✅ Tables in schema: {} successfully loaded".format(group[0].get("schema")))

            #Loop tables after insertion
            print("🔄 Loading {} constraints...".format(group[0].get("schema")))
            for table in tables:
                #Get current table id
                query = "SELECT * FROM query_orchestrator.tables WHERE name = '{}' AND \"schema\" = '{}'".format(table[0], schema[0][0])
                current_table = self.postgresql_utils.execute_query_with_return(query)

                #Get current table constraints
                query = self.postgresql_utils.load_query(file_name=TABLE_CONSTRAINTS_QUERY,schema=group[0].get("schema"),table=table[0])
                constraints = self.postgresql_utils.execute_query_with_return(query)
                #Insert constraints
                if(constraints):
                    #Get referenced table
                    query = "SELECT * FROM query_orchestrator.tables WHERE name = '{}' AND \"schema\" = '{}'".format(constraints[0][2].split(".")[1], schema[0][0])
                    referenced_table = self.postgresql_utils.execute_query_with_return(query)

                    query = "INSERT INTO query_orchestrator.constraints (name, \"table\", referenced_table, table_key, referenced_table_key) VALUES ('{}', '{}', '{}', '{}', '{}');".format(constraints[0][0], current_table[0][0], referenced_table[0][0], constraints[0][3], constraints[0][4])
                    self.postgresql_utils.execute_query_without_return(query)
            print("✅ Constraints in schema: {} successfully loaded".format(group[0].get("schema")))

        print("✅ Schema {} successfully loaded".format(group[0].get("schema")))

        print(postgre_rollback_generator.generate_delete_rollback("DELETE FROM test1.employees WHERE id = 1", self.postgresql_utils))
        print(postgre_rollback_generator.generate_insert_rollback("INSERT INTO test1.employees (\"name\", manager) VALUES('ALVARO', 1)"))
        print(postgre_rollback_generator.generate_update_rollback("UPDATE test1.employees SET \"manager\" = 2 WHERE \"name\" = 'ALVARO'", self.postgresql_utils))                


