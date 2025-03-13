from flask import jsonify
from app.postgre_rollback_generator import PostgreRollbackGenerator
from app.postgresql_utils import PostgresqlUtils


class PSQLExecutor:
    def __init__(self, config):
        self.config_gropus = config.get("groups")
        self.postgresql_utils = PostgresqlUtils(config)
        self.postgresql_utils.close_connection
        postgresql_utils_native = PostgresqlUtils(config)
        self.postgre_rollback_generator = PostgreRollbackGenerator(postgresql_utils_native)

    def execute_query(self, payload, roles):
        for group in self.config_gropus:
            if roles.get("name") and group[0].get("name") == payload.get("group"):
                query_type = self._get_query_type(payload.get("query"))
                rollback_query = ''
                if query_type == 'insert' and'write' in roles.get("name"):
                    try:
                        rollback_query = self.postgre_rollback_generator.generate_insert_rollback(payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while generating the rollback", "message":e}), 400
                    try:
                        self._insert_rollback(query=payload.get("query"), rollback=rollback_query)
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'delete' and 'write' in roles.get("name"):
                    try:
                        rollback_query = self.postgre_rollback_generator.generate_delete_rollback(payload.get("query"), self.postgresql_utils)
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while generating the rollback", "message":e}), 400
                    try:
                        self._insert_rollback(query=payload.get("query"), rollback=rollback_query)
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'update' and 'write' in roles.get("name"):
                    try:
                        rollback_query = self.postgre_rollback_generator.generate_update_rollback(payload.get("query"), self.postgresql_utils)
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while generating the rollback", "message":e}), 400
                    try:
                        self._insert_rollback(query=payload.get("query"), rollback=rollback_query)
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'select' and 'read' in roles.get("name"):
                    try:
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'other' and 'write' in roles.get("name"):
                    try:
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                else:
                    return jsonify({"error": "Unauthorized access"}), 403
            else:
                return jsonify({"error": "Unauthorized access"}), 403
            
            return jsonify({"message": "OK"}), 200

    def _execute_query_in_all_sources(self, group, query):
        for source in group:
            self.postgresql_utils.open_connection(source.get("db_name"), source.get("user"), source.get("password"), source.get("host"), source.get("port"))
            self.postgresql_utils.execute_query_without_return(query)
            self.postgresql_utils.close_connection()
    
    def _insert_rollback(self, query, rollback):
        self.postgresql_utils.execute_query_without_return("INSERT INTO query_orchestrator.history (\"query\", \"rollback\") VALUES ({}, {})".format(query,rollback))

    
    def _get_query_type(query: str) -> str:
        """
        Determines the type of SQL query based on the given query string.
        Parameters:
            query (str): The SQL query as a string.
        Returns:
            str: The type of query: "insert", "delete", "update", or "other".
        """
        # Remove leading/trailing whitespace and convert the string to lowercase
        trimmed_query = query.strip().lower()
        
        # Check if the query starts with the "insert" keyword
        if trimmed_query.startswith("insert"):
            return "insert"
        # Check if the query starts with the "delete" keyword
        elif trimmed_query.startswith("delete"):
            return "delete"
        # Check if the query starts with the "update" keyword
        elif trimmed_query.startswith("update"):
            return "update"
        # Check if the query starts with the "select" keyword
        elif trimmed_query.startswith("select"):
            return "select"
        # If none of the above, return "other"
        else:
            return "other"