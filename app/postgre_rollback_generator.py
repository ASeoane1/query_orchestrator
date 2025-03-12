class PostgreRollbackGenerator:
    def __init__(self, postgresql_utils_native):
        self.postgresql_utils_native = postgresql_utils_native

    # def generate_delete_rollback(self, query, postgresql_utils):
    #     """
    #     Generates a rollback for a given query.
        
    #     :param query: DELETE query
    #     :return: Rollback query
    #     """
    #     #Get table query
    #     try:
    #         table_name = query.split("FROM")[1].split()[0].strip()
    #     except IndexError:
    #         return "-- Unable to extract table name"
        
    #     # Get row data
    #     select_query = query.replace("DELETE", "SELECT *", 1)
    #     deleted_rows = postgresql_utils.execute_query_with_dict_return(select_query)
        
    #     if not deleted_rows:
    #         return "-- Unable to find data to be deleted"
        
    #     #Build rollback
    #     rollback_statements = []
    #     for row in deleted_rows:
    #         columns = ", ".join(row.keys())
    #         values = ", ".join([f"'{value}'" if isinstance(value, str) else str(value) for value in row.values()])
    #         rollback_statements.append(f"INSERT INTO {table_name} ({columns}) VALUES ({values});")
        
    #     return "\n".join(rollback_statements)

    def generate_delete_rollback(self, query, postgresql_utils):
        """
        Generates a rollback for a given DELETE query, considering cascading deletions.
        
        :param query: DELETE query
        :param postgresql_utils: Instance to execute queries
        :return: Rollback queries including cascading deletions
        """
        try:
            full_table_name = query.split("FROM")[1].split()[0].strip()
            if '.' in full_table_name:
                schema_name, table_name = full_table_name.split('.')
            else:
                schema_name, table_name = 'public', full_table_name
        except IndexError:
            return "-- Unable to extract table name"
        
        # Get row data before deletion
        select_query = query.replace("DELETE", "SELECT *", 1)
        deleted_rows = postgresql_utils.execute_query_with_dict_return(select_query)
        
        if not deleted_rows:
            return "-- Unable to find data to be deleted"
        
        rollback_statements = set()
        for row in deleted_rows:
            columns = ", ".join(row.keys())
            values = ", ".join([f"'{value}'" if isinstance(value, str) else str(value) for value in row.values()])
            rollback_statements.add(f"INSERT INTO {schema_name}.{table_name} ({columns}) VALUES ({values});")
        
        # Identify cascading deletions
        schema_query = f"""
            SELECT t.id 
            FROM query_orchestrator.tables t
            JOIN query_orchestrator.schemas s ON t.schema = s.id
            WHERE t.name = '{table_name}' AND s.name = '{schema_name}';
        """
        table_info = self.postgresql_utils_native.execute_query_with_dict_return(schema_query)
        
        if table_info:
            table_id = table_info[0]['id']
            cascade_query = f"SELECT referenced_table, table_key, referenced_table_key FROM query_orchestrator.constraints WHERE \"table\" = {table_id};"
            cascade_constraints = self.postgresql_utils_native.execute_query_with_dict_return(cascade_query)
            
            for constraint in cascade_constraints:
                referenced_table_id = constraint['referenced_table']
                ref_table_query = f"""
                    SELECT t.name, s.name AS schema_name 
                    FROM query_orchestrator.tables t
                    JOIN query_orchestrator.schemas s ON t.schema = s.id
                    WHERE t.id = {referenced_table_id};
                """
                ref_table_info = self.postgresql_utils_native.execute_query_with_dict_return(ref_table_query)
                
                if ref_table_info:
                    ref_table_name = ref_table_info[0]['name']
                    ref_schema_name = ref_table_info[0]['schema_name']
                    
                    ref_table_key = constraint['referenced_table_key']
                    table_key = constraint['table_key']

                    if table_id == referenced_table_id:
                        ref_table_key = table_key
                
                    for row in deleted_rows:
                        if table_key in row:
                            ref_select_query = f"SELECT * FROM {ref_schema_name}.{ref_table_name} WHERE {ref_table_key} = {row[table_key]};"
                            ref_deleted_rows = postgresql_utils.execute_query_with_dict_return(ref_select_query)
                            
                            for ref_row in ref_deleted_rows:
                                ref_columns = ", ".join(ref_row.keys())
                                ref_values = ", ".join([f"'{value}'" if isinstance(value, str) else str(value) for value in ref_row.values()])
                                rollback_statements.add(f"INSERT INTO {ref_schema_name}.{ref_table_name} ({ref_columns}) VALUES ({ref_values});")
        
        return "\n".join(sorted(rollback_statements))

    
    def generate_insert_rollback(self, query):
        """
        Generates a rollback SQL statement for an INSERT query by deleting inserted records.
        
        :param query: Executed INSERT query
        :return: SQL statement to revert the insertion
        """
        try:
            table_name = query.split("INTO")[1].split("(")[0].strip()
            columns_values_part = query.split("VALUES")[1].strip().strip(";")
            values_part = columns_values_part.strip("()")
            values = values_part.split(", ")
        except IndexError:
            return "-- Unable to extract table name or values"
        
        # Extract column names from the query
        columns_part = query.split("(")[1].split(")")[0]
        columns = columns_part.split(", ")
        
        # Generate DELETE condition
        conditions = " AND ".join([f'{columns[i]} = {values[i]}' if not values[i].startswith("'") else f'{columns[i]} = {values[i]}' for i in range(len(columns))])
        
        # Generate DELETE statement
        delete_query = f"DELETE FROM {table_name} WHERE {conditions};"
        
        return delete_query
    
    def generate_update_rollback(self, query, postgresql_utils):
        """
        Generates a rollback SQL statement for an UPDATE query by restoring previous values.
        
        :param query: Executed UPDATE query
        :param postgresql_utils: Instance to execute queries
        :return: SQL statements to revert the update
        """
        try:
            table_name = query.split("UPDATE")[1].split("SET")[0].strip()
            set_part = query.split("SET")[1].split("WHERE")[0].strip()
            where_part = query.split("WHERE")[1].strip().strip(";")
        except IndexError:
            return "-- Unable to extract table name, SET, or WHERE conditions"
        
        # Retrieve original values before the update
        select_query = f"SELECT * FROM {table_name} WHERE {where_part};"
        original_rows = postgresql_utils.execute_query_with_dict_return(select_query)
        
        if not original_rows:
            return "-- No matching records found to generate rollback"
        
        rollback_statements = []
        for row in original_rows:
            set_conditions = []
            where_conditions = []
            for column, value in row.items():
                if column in set_part:
                    set_conditions.append(f'{column} = {value!r}')
                else:
                    where_conditions.append(f'{column} = {value!r}')
            
            rollback_statements.append(f"UPDATE {table_name} SET {', '.join(set_conditions)} WHERE {' AND '.join(where_conditions)};")
        
        return "\n".join(rollback_statements)
