from flask import jsonify
from app.postgre_rollback_generator import PostgreRollbackGenerator
from app.postgresql_utils import PostgresqlUtils


class PSQLExecutor:
    def __init__(self, config):
        self.config_gropus = config.get("groups")
        self.postgresql_utils = PostgresqlUtils(config.get("native_database"))
        self.postgresql_utils.close_connection()
        self.postgresql_utils_native = PostgresqlUtils(config.get("native_database"))
        self.postgre_rollback_generator = PostgreRollbackGenerator(self.postgresql_utils_native)

    def execute_query(self, payload, roles):
        for group in self.config_gropus:
            if roles.get(group[0].get("name")) and group[0].get("name") == payload.get("group"):
                postgresql_utils = PostgresqlUtils(group[0])
                query_type = self._get_query_type(payload.get("query"))
                rollback_query = ''
                id = None
                if query_type == 'insert' and 'write' in roles.get(group[0].get("name")):
                    try:
                        if not payload.get("rollback"):
                            rollback_query = self.postgre_rollback_generator.generate_insert_rollback(payload.get("query"))
                        else:
                            rollback_query = payload.get("rollback")
                        id = self._insert_rollback(query=payload.get("query"), rollback=rollback_query)
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while generating the rollback", "message":e}), 400
                    try:
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'delete' and 'write' in roles.get(group[0].get("name")):
                    try:
                        if not payload.get("rollback"):
                            rollback_query = self.postgre_rollback_generator.generate_delete_rollback(payload.get("query"), postgresql_utils)
                        else:
                            rollback_query = payload.get("rollback")
                        id = self._insert_rollback(query=payload.get("query"), rollback=rollback_query)
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while generating the rollback", "message":e}), 400
                    try:
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'update' and 'write' in roles.get(group[0].get("name")):
                    try:
                        if not payload.get("rollback"):
                            rollback_query = self.postgre_rollback_generator.generate_update_rollback(payload.get("query"), postgresql_utils)
                        else:
                            rollback_query = payload.get("rollback")
                        id = self._insert_rollback(query=payload.get("query"), rollback=rollback_query)
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while generating the rollback", "message":e}), 400
                    try:
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'select' and 'read' in roles.get(group[0].get("name")):
                    try:
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'other' and 'write' in roles.get(group[0].get("name")):
                    try:
                        if payload.get("rollback"):
                            rollback_query = payload.get("rollback")
                        else:
                            rollback_query = ''
                        id = self._insert_rollback(query=payload.get("query"), rollback=rollback_query)
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                else:
                    return jsonify({"error": "Unauthorized access"}), 403
                postgresql_utils.close_connection()
            else:
                return jsonify({"error": "Unauthorized access"}), 403
            
            return jsonify({"message": "OK", "query_id":id}), 200
        
    def execute_rollback(self, payload, roles):
        for group in self.config_gropus:
            if roles.get(group[0].get("name")) and group[0].get("name") == payload.get("group"):
                record = self._get_rollback_by_id(payload.get("query_id"))
                id = None
                query_type = self._get_query_type(record.get("rollback"))
                if query_type == 'insert' and 'write' in roles.get(group[0].get("name")):
                    try:
                        id = self._insert_rollback(query=record.get("rollback"), rollback=record.get("query"))
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'delete' and 'write' in roles.get(group[0].get("name")):
                    try:
                        id = self._insert_rollback(query=record.get("rollback"), rollback=record.get("query"))
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'update' and 'write' in roles.get(group[0].get("name")):
                    try:
                        id = self._insert_rollback(query=record.get("rollback"), rollback=record.get("query"))
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'select' and 'read' in roles.get(group[0].get("name")):
                    try:
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                elif query_type == 'other' and 'write' in roles.get(group[0].get("name")):
                    try:
                        self._execute_query_in_all_sources(group=group,query=payload.get("query"))
                    except Exception as e:
                        return jsonify({"error": "Something went wrong while executing the query", "message":e}), 400
                else:
                    return jsonify({"error": "Unauthorized access"}), 403
            else:
                return jsonify({"error": "Unauthorized access"}), 403
            
            return jsonify({"message": "OK", "query_id":id}), 200

            

    def _get_rollback_by_id(self, id):
        return self.postgresql_utils_native.execute_query_with_dict_return("SELECT * FROM query_orchestrator.history WHERE id = {}".format(id))[0]

    def _execute_query_in_all_sources(self, group, query):
        for source in group:
            self.postgresql_utils.open_connection(source.get("dbname"), source.get("user"), source.get("password"), source.get("host"), source.get("port"))
            self.postgresql_utils.execute_query_without_return(query)
            self.postgresql_utils.close_connection()
    
    def _insert_rollback(self, query, rollback):
        return self.postgresql_utils_native.insert_rollback(query,rollback)

    
    def _get_query_type(self, query: str) -> str:
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