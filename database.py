from typing import Dict, List, Any, Optional, Union, Tuple
import sql_compiler as sc

class ColumnDef:
    def __init__(self, name: str, data_type: sc.TokenType):
        self.name = name
        self.type = data_type

class Table:
    def __init__(self, name: str, columns: List[ColumnDef], title: Optional[str] = None):
        self.name = name
        self.title = title if title else name
        self.columns = columns
        self.rows = []

    def add_row(self, values: List[Any]) -> bool:
        if len(values) != len(self.columns):
            print(f"Error: Column count mismatch. Expected {len(self.columns)}, got {len(values)}")
            return False
        for i, value in enumerate(values):
            if not self._validate_type(value, self.columns[i].type):
                print(f"Error: Type mismatch for column '{self.columns[i].name}'. Expected {self.columns[i].type}, got {type(value)}")
                return False
        self.rows.append(values)
        return True

    def _validate_type(self, value: Any, expected_type: sc.TokenType) -> bool:
        if value is None:
            return True
        if expected_type == sc.TokenType.INT:
            return isinstance(value, int)
        elif expected_type == sc.TokenType.FLOAT:
            return isinstance(value, (int, float))
        elif expected_type == sc.TokenType.TEXT:
            return isinstance(value, str)
        elif expected_type == sc.TokenType.DATE:
            # Assuming DATE is stored as a string for simplicity
            return isinstance(value, str)
        return False

    def get_column_index(self, column_name: str) -> int:
        for i, col in enumerate(self.columns):
            if col.name.lower() == column_name.lower():
                return i
        return -1

    def print_table(self, columns: Optional[List[int]] = None) -> None:
        print(f"\nTable: {self.title}\n")
        if not columns:
            columns = list(range(len(self.columns)))
        header = [self.columns[i].name for i in columns]
        print(" | ".join(header))
        print("-" * (sum(len(h) for h in header) + 3 * (len(header) - 1)))
        for row in self.rows:
            row_data = ["NULL" if row[i] is None else str(row[i]) for i in columns]
            print(" | ".join(row_data))

class Database:
    def __init__(self):
        self.tables: Dict[str, Table] = {}

    def create_table(self, name: str, columns: List[ColumnDef], title: Optional[str] = None) -> bool:
        if name.lower() in self.tables:
            print(f"Error: Table '{name}' already exists")
            return False
        self.tables[name.lower()] = Table(name, columns, title)
        return True
    
    def get_schema(self) -> dict:
        schema_dict = {}
        for table_name, table in self.tables.items():
            
           columns = []
           for idx, col in enumerate(table.columns):
              
              data_type_str = str(col.type).replace('TokenType.', '')
              columns.append({
                'name': col.name,
                'type': data_type_str,
                'index': idx
                 })
           schema_dict[table.name] = columns
        return schema_dict

    def get_schema_text(self) -> str:
        
        if not self.tables:
            return "Database is empty. No tables defined."

        schema_info = "Database Schema:\n"
        schema_info += "================\n\n"

        for table_name, table in self.tables.items():
            
            schema_info += f"Table: {table.title} ({table.name})\n"
            schema_info += "-" * (len(f"Table: {table.title} ({table.name})")) + "\n"
            
            columns = table.columns
            if not columns:
              schema_info += "  No columns defined.\n\n"
              continue

              # Header
            headers = ["Index", "Column Name", "Type"]
            widths = [6, 15, 10]
            schema_info += f"{headers[0]:<{widths[0]}} | {headers[1]:<{widths[1]}} | {headers[2]:<{widths[2]}}\n"
            schema_info += f"{'-'*widths[0]}-+-{'-'*widths[1]}-+-{'-'*widths[2]}\n"
            # Rows
            for idx, col in enumerate(columns):
               data_type_str = str(col.type).replace('TokenType.', "")
               schema_info += f"{idx:<{widths[0]}} | {col.name:<{widths[1]}} | {data_type_str:<{widths[2]}}\n"

            schema_info += f"\nTotal rows: {len(table.rows)}\n\n"

        return schema_info



    def drop_table(self, name: str) -> bool:
        if name.lower() not in self.tables:
            print(f"Error: Table '{name}' does not exist")
            return False
        del self.tables[name.lower()]
        return True
    
    def get_table(self, name: str) -> Optional[Table]:
        return self.tables.get(name.lower())
    

    def execute_query(self, ast: sc.ASTNode) -> Any: # Changed return type to Any to accommodate tuple for SELECT
        if ast.type == sc.NodeType.SELECT_STMT:
            return self._execute_select(ast)
        elif ast.type == sc.NodeType.INSERT_STMT:
            return self._execute_insert(ast)
        elif ast.type == sc.NodeType.UPDATE_STMT:
            return self._execute_update(ast)
        elif ast.type == sc.NodeType.DELETE_STMT:
            return self._execute_delete(ast)
        elif ast.type == sc.NodeType.CREATE_STMT:
            return self._execute_create(ast)
        elif ast.type == sc.NodeType.DROP_STMT:
            return self._execute_drop(ast)
        else:
            print(f"Error: Unsupported query type: {ast.type}")
            return False

    def _execute_select(self, ast: sc.ASTNode) -> Union[Tuple[List[str], List[List[Any]]], bool]: # Specify return type for SELECT
        if not ast.data.get('tables', []):
            print("Error: No table specified in SELECT statement")
            return False
        table_node = ast.data['tables'][0]
        table_name = table_node.data['name']
        table = self.get_table(table_name)
        if not table:
            print(f"Error: Table '{table_name}' not found")
            return False
        selected_columns_indices = []
        selected_column_names = [] # List to store selected column names for the header
        if ast.data['columns'][0].data['name'] == '*':
            selected_columns_indices = list(range(len(table.columns)))
            selected_column_names = [col.name for col in table.columns] # Get all column names
        else:
            for col_node in ast.data['columns']:
                # Ensure we get the string name for column lookup
                if col_node.type == sc.NodeType.IDENTIFIER:
                     col_name = col_node.data['name']
                elif col_node.type == sc.NodeType.EXPRESSION and col_node.data.get('operator') == sc.TokenType.DOT:
                     # Handle table.column format in SELECT
                     col_name = col_node.data['right'].data['name']
                else:
                     print(f"Error: Unsupported column reference in SELECT: {col_node.type}")
                     return False

                col_idx = table.get_column_index(col_name)
                if col_idx == -1:
                    print(f"Error: Column '{col_name}' not found in table '{table_name}'")
                    return False
                selected_columns_indices.append(col_idx)
                selected_column_names.append(col_name) # Add the selected column name

        filtered_rows = []
        for row in table.rows:
            if not ast.data.get('where_clause') or self._evaluate_condition(ast.data['where_clause'], table, row):
                # Create a new list with only the selected columns for the filtered row
                filtered_row_data = [row[i] for i in selected_columns_indices]
                filtered_rows.append(filtered_row_data)

        # Print what is being returned for debugging
        print(f"DEBUG: _execute_select returning columns: {selected_column_names}, rows: {filtered_rows}")

        # Return the column names and the filtered rows
        return selected_column_names, filtered_rows


    def _execute_insert(self, ast: sc.ASTNode) -> bool:
        table_name = ast.data['table'].data['name']
        table = self.get_table(table_name)
        if not table:
            print(f"Error: Table '{table_name}' not found")
            return False

        values_to_insert = [self._evaluate_expression(expr) for expr in ast.data['values']]

        if ast.data['columns']:
            column_indices = []
            for col_node in ast.data['columns']:
                # Ensure we get the string name for column lookup
                if col_node.type == sc.NodeType.IDENTIFIER:
                    col_name = col_node.data['name']
                else:
                    print(f"Error: Unsupported column reference in INSERT: {col_node.type}")
                    return False

                col_idx = table.get_column_index(col_name)
                if col_idx == -1:
                    print(f"Error: Column '{col_name}' not found in table '{table_name}'")
                    return False
                column_indices.append(col_idx)

            # Create a list with None for all columns, then fill in the specified ones
            row_values = [None] * len(table.columns)
            if len(column_indices) != len(values_to_insert):
                 print(f"Error: Column and value count mismatch. Expected {len(column_indices)} values, got {len(values_to_insert)}")
                 return False

            for i, col_idx in enumerate(column_indices):
                row_values[col_idx] = values_to_insert[i]

            if not table.add_row(row_values):
                return False
        else:
            # If no columns specified, assume values are in order of table columns
            if len(values_to_insert) != len(table.columns):
                 print(f"Error: Value count mismatch. Expected {len(table.columns)} values, got {len(values_to_insert)}")
                 return False
            if not table.add_row(values_to_insert):
                return False

        print("1 row inserted")
        return True


    def _execute_update(self, ast: sc.ASTNode) -> bool:
        table_name = ast.data['table'].data['name']
        table = self.get_table(table_name)
        if not table:
            print(f"Error: Table '{table_name}' not found")
            return False
        set_clauses = []
        for set_node in ast.data['set_clauses']:
            # Ensure we get the string name for column lookup
            if set_node.data['left'].type == sc.NodeType.IDENTIFIER:
                col_name = set_node.data['left'].data['name']
            else:
                print(f"Error: Unsupported column reference in UPDATE SET clause: {set_node.data['left'].type}")
                return False

            col_idx = table.get_column_index(col_name)
            if col_idx == -1:
                print(f"Error: Column '{col_name}' not found in table '{table_name}'")
                return False
            value = self._evaluate_expression(set_node.data['right'])
            set_clauses.append((col_idx, value))
        rows_updated = 0
        for row in table.rows:
            if not ast.data.get('where_clause') or self._evaluate_condition(ast.data['where_clause'], table, row):
                for col_idx, value in set_clauses:
                    # Validate type before updating
                    if not table._validate_type(value, table.columns[col_idx].type):
                         print(f"Error: Type mismatch for column '{table.columns[col_idx].name}' during update. Expected {table.columns[col_idx].type}, got {type(value)}")
                         return False
                    row[col_idx] = value
                rows_updated += 1
        print(f"{rows_updated} row(s) updated")
        return True

    def _execute_delete(self, ast: sc.ASTNode) -> bool:
        table_name = ast.data['table'].data['name']
        table = self.get_table(table_name)
        if not table:
            print(f"Error: Table '{table_name}' not found")
            return False
        rows_to_keep = []
        rows_deleted = 0
        for row in table.rows:
            if ast.data.get('where_clause') and not self._evaluate_condition(ast.data['where_clause'], table, row):
                rows_to_keep.append(row)
            else:
                rows_deleted += 1
        table.rows = rows_to_keep
        print(f"{rows_deleted} row(s) deleted")
        return True

    def _execute_create(self, ast: sc.ASTNode) -> bool:
        table_name = ast.data['table'].data['name']
        columns = []
        for col_node in ast.data['columns']:
            # Correctly extract the string name from the IDENTIFIER ASTNode
            if col_node.data['name'].type == sc.NodeType.IDENTIFIER:
                 col_name = col_node.data['name'].data['name']
            else:
                 print(f"Error: Unsupported column name format in CREATE TABLE: {col_node.data['name'].type}")
                 return False

            col_type = col_node.data['data_type']
            columns.append(ColumnDef(col_name, col_type))
        title = ast.data.get('title')
        if self.create_table(table_name, columns, title=title):
            print(f"Table '{table_name}' created")
            return True
        return False


    def _execute_drop(self, ast: sc.ASTNode) -> bool:
        table_name = ast.data['table'].data['name']
        if self.drop_table(table_name):
            print(f"Table '{table_name}' dropped")
            return True
        return False

    def _evaluate_condition(self, condition: sc.ASTNode, table: Table, row: List[Any]) -> Any: # Changed return type to Any for flexibility
        if condition.type == sc.NodeType.CONDITION:
            if 'operator' in condition.data and condition.data['operator'] == sc.TokenType.AND:
                left_eval = self._evaluate_condition(condition.data['left'], table, row)
                right_eval = self._evaluate_condition(condition.data['right'], table, row)
                # Handle potential non-boolean results from sub-conditions
                if isinstance(left_eval, bool) and isinstance(right_eval, bool):
                    return left_eval and right_eval
                else:
                     # Handle cases where sub-conditions don't evaluate to boolean, maybe treat as False or raise error
                     print(f"Warning: Non-boolean result in AND condition: {left_eval}, {right_eval}")
                     return False # Or handle as an error

            elif 'operator' in condition.data and condition.data['operator'] == sc.TokenType.OR:
                left_eval = self._evaluate_condition(condition.data['left'], table, row)
                right_eval = self._evaluate_condition(condition.data['right'], table, row)
                # Handle potential non-boolean results
                if isinstance(left_eval, bool) and isinstance(right_eval, bool):
                    return left_eval or right_eval
                else:
                     print(f"Warning: Non-boolean result in OR condition: {left_eval}, {right_eval}")
                     return False # Or handle as an error

            elif 'operator' in condition.data and condition.data['operator'] == sc.TokenType.NOT:
                right_eval = self._evaluate_condition(condition.data['right'], table, row)
                # Handle potential non-boolean results
                if isinstance(right_eval, bool):
                    return not right_eval
                else:
                    print(f"Warning: Non-boolean result in NOT condition: {right_eval}")
                    return False # Or handle as an error

            elif 'operator' in condition.data:
                left_value = self._evaluate_expression(condition.data['left'], table, row)
                right_value = self._evaluate_expression(condition.data['right'], table, row)
                op = condition.data['operator']
                # Add checks for comparable types
                if type(left_value) != type(right_value) and not (isinstance(left_value, (int, float)) and isinstance(right_value, (int, float))):
                     print(f"Error: Type mismatch in comparison: {type(left_value)} vs {type(right_value)}")
                     return False # Or raise an error

                if op == sc.TokenType.EQUALS: return left_value == right_value
                if op == sc.TokenType.NOT_EQUALS: return left_value != right_value
                if op == sc.TokenType.GREATER: return left_value > right_value
                if op == sc.TokenType.LESS: return left_value < right_value
                if op == sc.TokenType.GREATER_EQUALS: return left_value >= right_value
                if op == sc.TokenType.LESS_EQUALS: return left_value <= right_value
                print(f"Error: Unsupported operator: {op}")
                return False
        # If the condition is not a comparison or logical operation, evaluate it as an expression
        evaluated_expr = self._evaluate_expression(condition, table, row)
        # Treat non-boolean expression results in a condition context (e.g., a column name)
        # This might need more sophisticated handling depending on desired SQL behavior
        # For now, returning the evaluated expression, which might be truthy/falsy in Python
        return evaluated_expr


    def _evaluate_expression(self, expr: sc.ASTNode, table: Optional[Table] = None, row: Optional[List[Any]] = None) -> Any:
        if expr.type == sc.NodeType.IDENTIFIER:
            # If table and row are provided, try to resolve identifier as a column
            if table and row:
                col_idx = table.get_column_index(expr.data['name'])
                if col_idx != -1:
                    return row[col_idx]
            # Otherwise, return the identifier name (e.g., in CREATE TABLE)
            return expr.data['name']
        elif expr.type == sc.NodeType.LITERAL:
            return expr.data['value']
        elif expr.type == sc.NodeType.EXPRESSION:
            left_value = self._evaluate_expression(expr.data['left'], table, row)
            if expr.data['operator'] == sc.TokenType.DOT:
                right_value = self._evaluate_expression(expr.data['right'], table, row)
                # Handle table.column notation - assuming left_value is table name string
                if isinstance(left_value, str) and isinstance(right_value, str):
                    # In a real scenario, you'd use left_value to find the table
                    # For this in-memory DB, we'll just return the column name for now
                    # This part might need adjustment depending on how you intend to use table.column in expressions
                    return right_value # Returning the column name string
                else:
                     print(f"Error: Invalid operands for DOT operator: {type(left_value)}, {type(right_value)}")
                     return None # Or raise an error

            right_value = self._evaluate_expression(expr.data['right'], table, row)
            op = expr.data['operator']

            # Basic type checking for arithmetic operations
            if op in [sc.TokenType.PLUS, sc.TokenType.MINUS, sc.TokenType.ASTERISK, sc.TokenType.DIVIDE]:
                 if not isinstance(left_value, (int, float)) or not isinstance(right_value, (int, float)):
                      print(f"Error: Invalid types for arithmetic operation {op}: {type(left_value)}, {type(right_value)}")
                      return None # Or raise an error

            if op == sc.TokenType.PLUS: return left_value + right_value
            if op == sc.TokenType.MINUS: return left_value - right_value
            if op == sc.TokenType.ASTERISK: return left_value * right_value
            if op == sc.TokenType.DIVIDE:
                if right_value == 0:
                    print("Error: Division by zero")
                    return None # Or raise an error
                return left_value / right_value

            print(f"Error: Unsupported operator: {op}")
            return None
        else:
            print(f"Error: Unsupported expression type: {expr.type}")
            return None

class SQLGenerator:
    def __init__(self, db):
        self.db = db
        self.lexer = None
        self.parser = sc.Parser

    def execute_without_cursor(self, query: str):
        try:
            lexer = sc.Lexer(query)
            parser = self.parser(lexer)
            ast = parser.parse()

            # Consume the semicolon if present after parsing the statement
            if parser.current_token.type == sc.TokenType.SEMICOLON:
                parser.consume(sc.TokenType.SEMICOLON)
            # Check if there are remaining tokens after the statement and semicolon
            if parser.current_token.type != sc.TokenType.EOF:
                 print(f"Warning: Ignoring extra tokens after the first statement starting at line {parser.current_token.line}, column {parser.current_token.column}")


            result = self.db.execute_query(ast)
            return result

        except SyntaxError as e:
            print(f"Syntax Error: {str(e)}")
            return False
        except Exception as e:
           print(f"Execution error: {e}")
           return False

    def tokenize(self, query: str):
        self.lexer = sc.Lexer(query)
        token = self.lexer.get_next_token()
        tokens = []
        while token.type != sc.TokenType.EOF:
            tokens.append(token)
            token = self.lexer.get_next_token()
        return tokens

    def generate_sql(self, ast: sc.ASTNode) -> str:
        if ast.type == sc.NodeType.SELECT_STMT:
            return self.generate_select(ast)
        elif ast.type == sc.NodeType.INSERT_STMT:
            return self.generate_insert(ast)
        elif ast.type == sc.NodeType.UPDATE_STMT:
            return self.generate_update(ast)
        elif ast.type == sc.NodeType.DELETE_STMT:
            return self.generate_delete(ast)
        elif ast.type == sc.NodeType.CREATE_STMT:
            return self.generate_create(ast)
        elif ast.type == sc.NodeType.DROP_STMT:
            return self.generate_drop(ast)
        else:
            raise ValueError(f"Unsupported AST node type: {ast.type}")

    def generate_select(self, ast: sc.ASTNode) -> str:
        sql = "SELECT "
        sql += self.generate_column_list(ast.data['columns'])
        sql += " FROM "
        sql += self.generate_table_list(ast.data['tables'])

        if ast.data['joins']:
            for join in ast.data['joins']:
                sql += " " + self.generate_join(join)

        if ast.data['where_clause']:
            sql += " WHERE "
            sql += self.generate_condition(ast.data['where_clause'])

        return sql

    def generate_column_list(self, columns: List[sc.ASTNode]) -> str:
        if not columns:
            return "*"

        column_strs = []
        for column in columns:
            column_strs.append(self.generate_expression(column))

        return ", ".join(column_strs)

    def generate_table_list(self, tables: List[sc.ASTNode]) -> str:
        table_strs = []
        for table in tables:
            table_strs.append(self.generate_table_reference(table))

        return ", ".join(table_strs)

    def generate_table_reference(self, table: sc.ASTNode) -> str:
        return table.data['name']

    def generate_join(self, join: sc.ASTNode) -> str:
        sql = "JOIN "
        sql += self.generate_table_reference(join.data['table'])
        sql += " ON "
        sql += self.generate_condition(join.data['condition'])
        return sql

    def generate_condition(self, condition: sc.ASTNode) -> str:
        if condition.type == sc.NodeType.CONDITION:
            left = self.generate_expression(condition.data['left'])
            if 'operator' in condition.data and 'right' in condition.data:
                operator = self.token_type_to_string(condition.data['operator'])
                right = self.generate_expression(condition.data['right'])
                return f"{left} {operator} {right}"
            else:
                return left
        else:
            return self.generate_expression(condition)

    def generate_expression(self, expr: sc.ASTNode) -> str:
        if expr.type == sc.NodeType.IDENTIFIER:
            return expr.data['name']
        elif expr.type == sc.NodeType.LITERAL:
            return self.generate_literal(expr)
        elif expr.type == sc.NodeType.EXPRESSION:
            left = self.generate_expression(expr.data['left'])
            operator = self.token_type_to_string(expr.data['operator'])
            right = self.generate_expression(expr.data['right'])
            return f"{left} {operator} {right}"
        else:
            raise ValueError(f"Unsupported expression node type: {expr.type}")

    def generate_literal(self, literal: sc.ASTNode) -> str:
        if literal.data['value_type'] == sc.TokenType.INTEGER:
            return str(literal.data['value'])
        elif literal.data['value_type'] == sc.TokenType.FLOAT_LITERAL:
            return str(literal.data['value'])
        elif literal.data['value_type'] == sc.TokenType.STRING:
            return f"'{literal.data['value']}'"
        elif literal.data['value_type'] == sc.TokenType.NULL:
            return "NULL"
        else:
            raise ValueError(f"Unsupported literal type: {literal.data['value_type']}")

    def generate_insert(self, ast: sc.ASTNode) -> str:
        sql = "INSERT INTO "
        sql += self.generate_table_reference(ast.data['table'])

        if ast.data['columns']:
            sql += " ("
            sql += self.generate_column_list(ast.data['columns'])
            sql += ")"

        sql += " VALUES ("
        value_strs = []
        for value in ast.data['values']:
            value_strs.append(self.generate_expression(value))
        sql += ", ".join(value_strs)
        sql += ")"

        return sql

    def generate_update(self, ast: sc.ASTNode) -> str:
        sql = "UPDATE "
        sql += self.generate_table_reference(ast.data['table'])

        sql += " SET "
        set_strs = []
        for set_clause in ast.data['set_clauses']:
            left = self.generate_expression(set_clause.data['left'])
            right = self.generate_expression(set_clause.data['right'])
            set_strs.append(f"{left} = {right}")
        sql += ", ".join(set_strs)

        if ast.data['where_clause']:
            sql += " WHERE "
            sql += self.generate_condition(ast.data['where_clause'])

        return sql

    def generate_delete(self, ast: sc.ASTNode) -> str:
        sql = "DELETE FROM "
        sql += self.generate_table_reference(ast.data['table'])

        if ast.data['where_clause']:
            sql += " WHERE "
            sql += self.generate_condition(ast.data['where_clause'])

        return sql

    def generate_create(self, ast: sc.ASTNode) -> str:
        sql = "CREATE TABLE "
        sql += self.generate_table_reference(ast.data['table'])

        sql += " ("
        column_strs = []
        for column in ast.data['columns']:
            column_strs.append(self.generate_column_definition(column))
        sql += ", ".join(column_strs)
        sql += ")"

        return sql

    def generate_column_definition(self, column: sc.ASTNode) -> str:
        # Ensure we get the string name from the IDENTIFIER ASTNode
        if column.data['name'].type == sc.NodeType.IDENTIFIER:
             sql = column.data['name'].data['name']
        else:
             raise ValueError(f"Unsupported column name format in CREATE TABLE: {column.data['name'].type}")

        sql += " " + self.token_type_to_string(column.data['data_type'])
        return sql


    def execute(self, query: str):
        # This method seems to be a simplified execution and might not be used
        # in the main UI flow, but keeping it for completeness.
        try:
            if query.strip().lower().startswith("select"):
                table_name = query.split(' ')[3]
                table = self.db.get_table(table_name)
                if not table:
                    raise ValueError(f"Table '{table_name}' not found.")
                rows = table.rows
                columns = [col.name for col in table.columns]
                return columns, rows

            elif query.strip().lower().startswith("insert"):
                table_name = query.split(' ')[2]
                table = self.db.get_table(table_name)
                if not table:
                    raise ValueError(f"Table '{table_name}' not found.")
                # This part is hardcoded and likely needs to be dynamic based on parsed values
                values = [1, "example"]
                table.add_row(values)
                return 1

            elif query.strip().lower().startswith("update"):
                # Placeholder for update execution
                return 1

            elif query.strip().lower().startswith("delete"):
                # Placeholder for delete execution
                return 1

        except Exception as e:
            raise e


    def generate_drop(self, ast: sc.ASTNode) -> str:
        sql = "DROP TABLE "
        sql += self.generate_table_reference(ast.data['table'])
        return sql

    def token_type_to_string(self, token_type: sc.TokenType) -> str:
        token_strings = {
            sc.TokenType.SELECT: "SELECT",
            sc.TokenType.FROM: "FROM",
            sc.TokenType.WHERE: "WHERE",
            sc.TokenType.INSERT: "INSERT",
            sc.TokenType.INTO: "INTO",
            sc.TokenType.VALUES: "VALUES",
            sc.TokenType.UPDATE: "UPDATE",
            sc.TokenType.SET: "SET",
            sc.TokenType.DELETE: "DELETE",
            sc.TokenType.CREATE: "CREATE",
            sc.TokenType.TABLE: "TABLE",
            sc.TokenType.DROP: "DROP",
            sc.TokenType.JOIN: "JOIN",
            sc.TokenType.ON: "ON",
            sc.TokenType.AND: "AND",
            sc.TokenType.OR: "OR",
            sc.TokenType.NOT: "NOT",
            sc.TokenType.NULL: "NULL",
            sc.TokenType.INT: "INT",
            sc.TokenType.TEXT: "TEXT",
            sc.TokenType.FLOAT: "FLOAT",
            sc.TokenType.DATE: "DATE",
            sc.TokenType.EQUALS: "=",
            sc.TokenType.GREATER: ">",
            sc.TokenType.LESS: "<",
            sc.TokenType.GREATER_EQUALS: ">=",
            sc.TokenType.LESS_EQUALS: "<=",
            sc.TokenType.NOT_EQUALS: "!=",
            sc.TokenType.PLUS: "+",
            sc.TokenType.MINUS: "-",
            sc.TokenType.ASTERISK: "*",
            sc.TokenType.DIVIDE: "/",
            sc.TokenType.COMMA: ",",
            sc.TokenType.SEMICOLON: ";",
            sc.TokenType.LEFT_PAREN: "(",
            sc.TokenType.RIGHT_PAREN: ")",
            sc.TokenType.DOT: "."
        }

        return token_strings.get(token_type, str(token_type))
