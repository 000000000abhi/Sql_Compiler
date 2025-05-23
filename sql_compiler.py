import re
import sys
from enum import Enum, auto
from typing import Dict, List, Optional, Union, Any, Tuple

# Token types
class TokenType(Enum):
    # Keywords
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    UPDATE = auto()
    SET = auto()
    DELETE = auto()
    CREATE = auto()
    TABLE = auto()
    DROP = auto()
    JOIN = auto()
    ON = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    NULL = auto()
    INT = auto()
    TEXT = auto()
    FLOAT = auto()
    DATE = auto()

    # Operators
    EQUALS = auto()
    GREATER = auto()
    LESS = auto()
    GREATER_EQUALS = auto()
    LESS_EQUALS = auto()
    NOT_EQUALS = auto()
    PLUS = auto()
    MINUS = auto()
    ASTERISK = auto()
    DIVIDE = auto()

    # Punctuation
    COMMA = auto()
    SEMICOLON = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    DOT = auto()

    # Other
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT_LITERAL = auto()
    STRING = auto()
    EOF = auto()
    ERROR = auto()

# Token structure
class Token:
    def __init__(self, type: TokenType, lexeme: str, line: int, column: int):
        self.type = type
        self.lexeme = lexeme
        self.line = line
        self.column = column

    def __str__(self):
        return f"Token({self.type}, '{self.lexeme}', line={self.line}, col={self.column})"

# AST node types
class NodeType(Enum):
    SELECT_STMT = auto()
    INSERT_STMT = auto()
    UPDATE_STMT = auto()
    DELETE_STMT = auto()
    CREATE_STMT = auto()
    DROP_STMT = auto()
    COLUMN_LIST = auto()
    TABLE_REF = auto()
    JOIN = auto()
    WHERE_CLAUSE = auto()
    CONDITION = auto()
    EXPRESSION = auto()
    COLUMN_DEF = auto()
    LITERAL = auto()
    IDENTIFIER = auto()

# AST node structure
class ASTNode:
    def __init__(self, type: NodeType):
        self.type = type
        self.data = {}

    def __str__(self):
        return f"ASTNode({self.type}, {self.data})"

# Lexer class
class Lexer:
    def __init__(self, input_text: str):
        self.input = input_text
        self.position = 0
        self.line = 1
        self.column = 1
        self.keywords = {
            'select': TokenType.SELECT,
            'from': TokenType.FROM,
            'where': TokenType.WHERE,
            'insert': TokenType.INSERT,
            'into': TokenType.INTO,
            'values': TokenType.VALUES,
            'update': TokenType.UPDATE,
            'set': TokenType.SET,
            'delete': TokenType.DELETE,
            'create': TokenType.CREATE,
            'table': TokenType.TABLE,
            'drop': TokenType.DROP,
            'join': TokenType.JOIN,
            'on': TokenType.ON,
            'and': TokenType.AND,
            'or': TokenType.OR,
            'not': TokenType.NOT,
            'null': TokenType.NULL,
            'int': TokenType.INT,
            'text': TokenType.TEXT,
            'float': TokenType.FLOAT,
            'date': TokenType.DATE
        }

    def peek(self) -> str:
        if self.position >= len(self.input):
            return '\0'
        return self.input[self.position]

    def advance(self) -> str:
        char = self.peek()
        self.position += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def skip_whitespace(self):
        while self.peek().isspace():
            self.advance()

    def skip_comment(self):
        if self.peek() == '#':
            while self.peek() != '\n' and self.peek() != '\0':
                self.advance()

    def get_next_token(self) -> Token:
        self.skip_whitespace()
        self.skip_comment()

        # Check for EOF
        if self.position >= len(self.input):
            return Token(TokenType.EOF, "", self.line, self.column)

        char = self.peek()

        # Identifiers and keywords
        if char.isalpha() or char == '_':
            return self.identifier()

        # Numbers
        if char.isdigit():
            return self.number()

        # Strings
        if char == "'" or char == '"':
            return self.string()

        # Operators and punctuation
        if char == '=':
            self.advance()
            return Token(TokenType.EQUALS, "=", self.line, self.column - 1)

        if char == '>':
            self.advance()
            if self.peek() == '=':
                self.advance()
                return Token(TokenType.GREATER_EQUALS, ">=", self.line, self.column - 2)
            return Token(TokenType.GREATER, ">", self.line, self.column - 1)

        if char == '<':
            self.advance()
            if self.peek() == '=':
                self.advance()
                return Token(TokenType.LESS_EQUALS, "<=", self.line, self.column - 2)
            return Token(TokenType.LESS, "<", self.line, self.column - 1)

        if char == '!':
            self.advance()
            if self.peek() == '=':
                self.advance()
                return Token(TokenType.NOT_EQUALS, "!=", self.line, self.column - 2)
            return Token(TokenType.ERROR, "!", self.line, self.column - 1)

        if char == '+':
            self.advance()
            return Token(TokenType.PLUS, "+", self.line, self.column - 1)

        if char == '-':
            self.advance()
            return Token(TokenType.MINUS, "-", self.line, self.column - 1)

        if char == '*':
            self.advance()
            return Token(TokenType.ASTERISK, "*", self.line, self.column - 1)

        if char == '/':
            self.advance()
            return Token(TokenType.DIVIDE, "/", self.line, self.column - 1)

        if char == ',':
            self.advance()
            return Token(TokenType.COMMA, ",", self.line, self.column - 1)

        if char == ';':
            self.advance()
            return Token(TokenType.SEMICOLON, ";", self.line, self.column - 1)

        if char == '(':
            self.advance()
            return Token(TokenType.LEFT_PAREN, "(", self.line, self.column - 1)

        if char == ')':
            self.advance()
            return Token(TokenType.RIGHT_PAREN, ")", self.line, self.column - 1)

        if char == '.':
            self.advance()
            return Token(TokenType.DOT, ".", self.line, self.column - 1)

        # Unrecognized character
        self.advance()
        return Token(TokenType.ERROR, char, self.line, self.column - 1)

    def identifier(self) -> Token:
        start_column = self.column
        lexeme = ""

        while self.peek().isalnum() or self.peek() == '_':
            lexeme += self.advance()

        # Check if it's a keyword
        token_type = self.keywords.get(lexeme.lower(), TokenType.IDENTIFIER)

        return Token(token_type, lexeme, self.line, start_column)

    def number(self) -> Token:
        start_column = self.column
        lexeme = ""
        is_float = False

        while self.peek().isdigit() or self.peek() == '.':
            if self.peek() == '.':
                if is_float:  # Second decimal point is invalid
                    break
                is_float = True
            lexeme += self.advance()

        if is_float:
            return Token(TokenType.FLOAT_LITERAL, lexeme, self.line, start_column)
        else:
            return Token(TokenType.INTEGER, lexeme, self.line, start_column)

    def string(self) -> Token:
        start_column = self.column
        quote = self.advance()  # Get the opening quote
        lexeme = ""

        while self.peek() != quote and self.peek() != '\0':
            lexeme += self.advance()

        if self.peek() == '\0':
            return Token(TokenType.ERROR, lexeme, self.line, start_column)

        self.advance()  # Consume the closing quote
        return Token(TokenType.STRING, lexeme, self.line, start_column)

# Parser class
class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def consume(self, expected_type: TokenType) -> Token:
        if self.current_token.type == expected_type:
            token = self.current_token
            self.current_token = self.lexer.get_next_token()
            return token
        else:
            raise SyntaxError(f"Expected {expected_type}, got {self.current_token.type} at line {self.current_token.line}, column {self.current_token.column}")

    def parse_statement(self) -> Optional[ASTNode]:
        # This method parses a single SQL statement
        if self.current_token.type == TokenType.EOF:
            return None # No more statements

        return self.sql_statement()

    def sql_statement(self) -> ASTNode:
        if self.current_token.type == TokenType.SELECT:
            return self.select_statement()
        elif self.current_token.type == TokenType.INSERT:
            return self.insert_statement()
        elif self.current_token.type == TokenType.UPDATE:
            return self.update_statement()
        elif self.current_token.type == TokenType.DELETE:
            return self.delete_statement()
        elif self.current_token.type == TokenType.CREATE:
            return self.create_statement()
        elif self.current_token.type == TokenType.DROP:
            return self.drop_statement()
        else:
            raise SyntaxError(f"Unexpected token {self.current_token.type} at line {self.current_token.line}, column {self.current_token.column}")

    def select_statement(self) -> ASTNode:
        node = ASTNode(NodeType.SELECT_STMT)

        self.consume(TokenType.SELECT)
        node.data['columns'] = self.column_list()

        self.consume(TokenType.FROM)
        node.data['tables'] = self.table_list()

        # Optional JOIN clause
        node.data['joins'] = []
        while self.current_token.type == TokenType.JOIN:
            node.data['joins'].append(self.join_clause())

        # Optional WHERE clause
        if self.current_token.type == TokenType.WHERE:
            self.consume(TokenType.WHERE)
            node.data['where_clause'] = self.condition()
        else:
            node.data['where_clause'] = None

        return node

    def column_list(self) -> List[ASTNode]:
        columns = []

        if self.current_token.type == TokenType.ASTERISK:
            # SELECT *
            asterisk_node = ASTNode(NodeType.IDENTIFIER)
            asterisk_node.data['name'] = "*"
            columns.append(asterisk_node)
            self.consume(TokenType.ASTERISK)
        else:
            # SELECT col1, col2, ...
            columns.append(self.expression())

            while self.current_token.type == TokenType.COMMA:
                self.consume(TokenType.COMMA)
                columns.append(self.expression())

        return columns

    def table_list(self) -> List[ASTNode]:
        tables = []

        # FROM table1, table2, ...
        tables.append(self.table_reference())

        while self.current_token.type == TokenType.COMMA:
            self.consume(TokenType.COMMA)
            tables.append(self.table_reference())

        return tables

    def table_reference(self) -> ASTNode:
        node = ASTNode(NodeType.TABLE_REF)

        if self.current_token.type == TokenType.IDENTIFIER:
            node.data['name'] = self.current_token.lexeme
            self.consume(TokenType.IDENTIFIER)
        else:
            raise SyntaxError(f"Expected table name, got {self.current_token.type} at line {self.current_token.line}, column {self.current_token.column}")

        return node

    def join_clause(self) -> ASTNode:
        node = ASTNode(NodeType.JOIN)

        self.consume(TokenType.JOIN)
        node.data['table'] = self.table_reference()

        self.consume(TokenType.ON)
        node.data['condition'] = self.condition()

        return node

    def condition(self) -> ASTNode:
        node = self.expression()

        if self.current_token.type in [TokenType.EQUALS, TokenType.NOT_EQUALS,
                                      TokenType.GREATER, TokenType.LESS,
                                      TokenType.GREATER_EQUALS, TokenType.LESS_EQUALS]:
            operator_type = self.current_token.type
            self.consume(operator_type)

            right = self.expression()

            condition_node = ASTNode(NodeType.CONDITION)
            condition_node.data['left'] = node
            condition_node.data['operator'] = operator_type
            condition_node.data['right'] = right

            node = condition_node

        # Check for AND/OR
        while self.current_token.type in [TokenType.AND, TokenType.OR]:
            operator_type = self.current_token.type
            self.consume(operator_type)

            right = self.condition()

            condition_node = ASTNode(NodeType.CONDITION)
            condition_node.data['left'] = node
            condition_node.data['operator'] = operator_type
            condition_node.data['right'] = right

            node = condition_node

        return node

    def expression(self) -> ASTNode:
        if self.current_token.type == TokenType.IDENTIFIER:
            node = ASTNode(NodeType.IDENTIFIER)
            node.data['name'] = self.current_token.lexeme
            self.consume(TokenType.IDENTIFIER)

            # Check for table.column notation
            if self.current_token.type == TokenType.DOT:
                self.consume(TokenType.DOT)

                if self.current_token.type == TokenType.IDENTIFIER:
                    column_node = ASTNode(NodeType.IDENTIFIER)
                    column_node.data['name'] = self.current_token.lexeme
                    self.consume(TokenType.IDENTIFIER)

                    expr_node = ASTNode(NodeType.EXPRESSION)
                    expr_node.data['left'] = node
                    expr_node.data['operator'] = TokenType.DOT
                    expr_node.data['right'] = column_node

                    node = expr_node
                else:
                    raise SyntaxError(f"Expected column name after dot, got {self.current_token.type}")

            return node
        elif self.current_token.type in [TokenType.INTEGER, TokenType.FLOAT_LITERAL, TokenType.STRING, TokenType.NULL]:
            return self.literal()
        elif self.current_token.type == TokenType.LEFT_PAREN:
            self.consume(TokenType.LEFT_PAREN)
            node = self.expression()
            self.consume(TokenType.RIGHT_PAREN)
            return node
        else:
            raise SyntaxError(f"Unexpected token in expression: {self.current_token.type}")

    def literal(self) -> ASTNode:
        node = ASTNode(NodeType.LITERAL)

        if self.current_token.type == TokenType.INTEGER:
            node.data['value_type'] = TokenType.INTEGER
            node.data['value'] = int(self.current_token.lexeme)
            self.consume(TokenType.INTEGER)
        elif self.current_token.type == TokenType.FLOAT_LITERAL:
            node.data['value_type'] = TokenType.FLOAT_LITERAL
            node.data['value'] = float(self.current_token.lexeme)
            self.consume(TokenType.FLOAT_LITERAL)
        elif self.current_token.type == TokenType.STRING:
            node.data['value_type'] = TokenType.STRING
            node.data['value'] = self.current_token.lexeme
            self.consume(TokenType.STRING)
        elif self.current_token.type == TokenType.NULL:
            node.data['value_type'] = TokenType.NULL
            node.data['value'] = None
            self.consume(TokenType.NULL)
        else:
            raise SyntaxError(f"Expected literal, got {self.current_token.type}")

        return node

    def insert_statement(self) -> ASTNode:
        node = ASTNode(NodeType.INSERT_STMT)

        self.consume(TokenType.INSERT)
        self.consume(TokenType.INTO)

        if self.current_token.type == TokenType.IDENTIFIER:
            table_node = ASTNode(NodeType.IDENTIFIER)
            table_node.data['name'] = self.current_token.lexeme
            node.data['table'] = table_node
            self.consume(TokenType.IDENTIFIER)
        else:
            raise SyntaxError(f"Expected table name, got {self.current_token.type}")

        # Optional column list
        if self.current_token.type == TokenType.LEFT_PAREN:
            self.consume(TokenType.LEFT_PAREN)
            node.data['columns'] = self.column_list()
            self.consume(TokenType.RIGHT_PAREN)
        else:
            node.data['columns'] = []

        self.consume(TokenType.VALUES)
        self.consume(TokenType.LEFT_PAREN)

        node.data['values'] = []
        node.data['values'].append(self.expression())

        while self.current_token.type == TokenType.COMMA:
            self.consume(TokenType.COMMA)
            node.data['values'].append(self.expression())

        self.consume(TokenType.RIGHT_PAREN)

        return node

    def update_statement(self) -> ASTNode:
        node = ASTNode(NodeType.UPDATE_STMT)

        self.consume(TokenType.UPDATE)

        if self.current_token.type == TokenType.IDENTIFIER:
            table_node = ASTNode(NodeType.IDENTIFIER)
            table_node.data['name'] = self.current_token.lexeme
            node.data['table'] = table_node
            self.consume(TokenType.IDENTIFIER)
        else:
            raise SyntaxError(f"Expected table name, got {self.current_token.type}")

        self.consume(TokenType.SET)

        node.data['set_clauses'] = []

        # First set clause
        set_clause = ASTNode(NodeType.EXPRESSION)

        if self.current_token.type == TokenType.IDENTIFIER:
            column_node = ASTNode(NodeType.IDENTIFIER)
            column_node.data['name'] = self.current_token.lexeme
            set_clause.data['left'] = column_node
            self.consume(TokenType.IDENTIFIER)
        else:
            raise SyntaxError(f"Expected column name, got {self.current_token.type}")

        self.consume(TokenType.EQUALS)
        set_clause.data['operator'] = TokenType.EQUALS
        set_clause.data['right'] = self.expression()

        node.data['set_clauses'].append(set_clause)

        # Additional set clauses
        while self.current_token.type == TokenType.COMMA:
            self.consume(TokenType.COMMA)

            set_clause = ASTNode(NodeType.EXPRESSION)

            if self.current_token.type == TokenType.IDENTIFIER:
                column_node = ASTNode(NodeType.IDENTIFIER)
                column_node.data['name'] = self.current_token.lexeme
                set_clause.data['left'] = column_node
                self.consume(TokenType.IDENTIFIER)
            else:
                raise SyntaxError(f"Expected column name, got {self.current_token.type}")

            self.consume(TokenType.EQUALS)
            set_clause.data['operator'] = TokenType.EQUALS
            set_clause.data['right'] = self.expression()

            node.data['set_clauses'].append(set_clause)

        # Optional WHERE clause
        if self.current_token.type == TokenType.WHERE:
            self.consume(TokenType.WHERE)
            node.data['where_clause'] = self.condition()
        else:
            node.data['where_clause'] = None

        return node

    def delete_statement(self) -> ASTNode:
        node = ASTNode(NodeType.DELETE_STMT)

        self.consume(TokenType.DELETE)
        self.consume(TokenType.FROM)

        if self.current_token.type == TokenType.IDENTIFIER:
            table_node = ASTNode(NodeType.IDENTIFIER)
            table_node.data['name'] = self.current_token.lexeme
            node.data['table'] = table_node
            self.consume(TokenType.IDENTIFIER)
        else:
            raise SyntaxError(f"Expected table name, got {self.current_token.type}")

        # Optional WHERE clause
        if self.current_token.type == TokenType.WHERE:
            self.consume(TokenType.WHERE)
            node.data['where_clause'] = self.condition()
        else:
            node.data['where_clause'] = None

        return node

    def create_statement(self) -> ASTNode:
        node = ASTNode(NodeType.CREATE_STMT)

        self.consume(TokenType.CREATE)
        self.consume(TokenType.TABLE)

        if self.current_token.type == TokenType.IDENTIFIER:
            table_node = ASTNode(NodeType.IDENTIFIER)
            table_node.data['name'] = self.current_token.lexeme
            node.data['table'] = table_node
            self.consume(TokenType.IDENTIFIER)
        else:
            raise SyntaxError(f"Expected table name, got {self.current_token.type}")

        self.consume(TokenType.LEFT_PAREN)

        node.data['columns'] = []

        # First column definition
        node.data['columns'].append(self.column_definition())

        # Additional column definitions
        while self.current_token.type == TokenType.COMMA:
            self.consume(TokenType.COMMA)
            node.data['columns'].append(self.column_definition())

        self.consume(TokenType.RIGHT_PAREN)

        return node

    def column_definition(self) -> ASTNode:
        node = ASTNode(NodeType.COLUMN_DEF)

        if self.current_token.type == TokenType.IDENTIFIER:
            name_node = ASTNode(NodeType.IDENTIFIER)
            name_node.data['name'] = self.current_token.lexeme
            node.data['name'] = name_node
            self.consume(TokenType.IDENTIFIER)
        else:
            raise SyntaxError(f"Expected column name, got {self.current_token.type}")

        if self.current_token.type in [TokenType.INT, TokenType.TEXT, TokenType.FLOAT, TokenType.DATE]:
            node.data['data_type'] = self.current_token.type
            self.consume(self.current_token.type)
        else:
            raise SyntaxError(f"Expected data type, got {self.current_token.type}")

        # Optional constraints (not implemented for simplicity)

        return node

    def drop_statement(self) -> ASTNode:
        node = ASTNode(NodeType.DROP_STMT)

        self.consume(TokenType.DROP)
        self.consume(TokenType.TABLE)

        if self.current_token.type == TokenType.IDENTIFIER:
            table_node = ASTNode(NodeType.IDENTIFIER)
            table_node.data['name'] = self.current_token.lexeme
            node.data['table'] = table_node
            self.consume(TokenType.IDENTIFIER)
        else:
            raise SyntaxError(f"Expected table name, got {self.current_token.type}")

        return node

# SQL Generator
class SQLGenerator:
    def __init__(self, db):
        self.db = db
        self.lexer = None
        self.parser = Parser

    def execute_without_cursor(self, query: str):
        results = []
        lexer = Lexer(query)
        parser = self.parser(lexer)

        while parser.current_token.type != TokenType.EOF:
            try:
                ast = parser.parse_statement()
                if ast:
                    result = self.db.execute_query(ast)
                    results.append(result)

                # Consume semicolon if present after a statement
                if parser.current_token.type == TokenType.SEMICOLON:
                    parser.consume(TokenType.SEMICOLON)

            except SyntaxError as e:
                print(f"Syntax Error: {str(e)}")
                results.append(False) # Indicate failure for this statement
                # Attempt to recover by advancing the lexer past the current token
                # This might not always work for complex errors but can help with simple ones
                parser.current_token = parser.lexer.get_next_token()
                # Skip the rest of the line to try and parse the next statement
                while parser.current_token.type not in [TokenType.SEMICOLON, TokenType.EOF]:
                     parser.current_token = parser.lexer.get_next_token()
                 # Consume the semicolon if we stopped at one
                if parser.current_token.type == TokenType.SEMICOLON:
                    parser.consume(TokenType.SEMICOLON)


            except Exception as e:
               print(f"Execution error: {e}")
               results.append(False) # Indicate failure for this statement
               # Attempt to skip to the next semicolon or EOF on execution error
               while parser.current_token.type not in [TokenType.SEMICOLON, TokenType.EOF]:
                    parser.current_token = parser.lexer.get_next_token()
               if parser.current_token.type == TokenType.SEMICOLON:
                   parser.consume(TokenType.SEMICOLON)

        # For simplicity in the UI, return the result of the last executed statement
        # In a real application, you might return all results
        if results:
            return results[-1]
        return None # Or some other indicator for no statements executed


    def tokenize(self, query: str):
        self.lexer = Lexer(query)
        token = self.lexer.get_next_token()
        tokens = []
        while token.type != TokenType.EOF:
            tokens.append(token)
            token = self.lexer.get_next_token()
        return tokens

    def generate_sql(self, ast: ASTNode) -> str:
        if ast.type == NodeType.SELECT_STMT:
            return self.generate_select(ast)
        elif ast.type == NodeType.INSERT_STMT:
            return self.generate_insert(ast)
        elif ast.type == NodeType.UPDATE_STMT:
            return self.generate_update(ast)
        elif ast.type == NodeType.DELETE_STMT:
            return self.generate_delete(ast)
        elif ast.type == NodeType.CREATE_STMT:
            return self.generate_create(ast)
        elif ast.type == NodeType.DROP_STMT:
            return self.generate_drop(ast)
        else:
            raise ValueError(f"Unsupported AST node type: {ast.type}")

    def generate_select(self, ast: ASTNode) -> str:
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

    def generate_column_list(self, columns: List[ASTNode]) -> str:
        if not columns:
            return "*"

        column_strs = []
        for column in columns:
            column_strs.append(self.generate_expression(column))

        return ", ".join(column_strs)

    def generate_table_list(self, tables: List[ASTNode]) -> str:
        table_strs = []
        for table in tables:
            table_strs.append(self.generate_table_reference(table))

        return ", ".join(table_strs)

    def generate_table_reference(self, table: ASTNode) -> str:
        return table.data['name']

    def generate_join(self, join: ASTNode) -> str:
        sql = "JOIN "
        sql += self.generate_table_reference(join.data['table'])
        sql += " ON "
        sql += self.generate_condition(join.data['condition'])
        return sql

    def generate_condition(self, condition: ASTNode) -> str:
        if condition.type == NodeType.CONDITION:
            left = self.generate_expression(condition.data['left'])
            if 'operator' in condition.data and 'right' in condition.data:
                operator = self.token_type_to_string(condition.data['operator'])
                right = self.generate_expression(condition.data['right'])
                return f"{left} {operator} {right}"
            else:
                return left
        else:
            return self.generate_expression(condition)

    def generate_expression(self, expr: ASTNode) -> str:
        if expr.type == NodeType.IDENTIFIER:
            return expr.data['name']
        elif expr.type == NodeType.LITERAL:
            return self.generate_literal(expr)
        elif expr.type == NodeType.EXPRESSION:
            left = self.generate_expression(expr.data['left'])
            operator = self.token_type_to_string(expr.data['operator'])
            right = self.generate_expression(expr.data['right'])
            return f"{left} {operator} {right}"
        else:
            raise ValueError(f"Unsupported expression node type: {expr.type}")

    def generate_literal(self, literal: ASTNode) -> str:
        if literal.data['value_type'] == TokenType.INTEGER:
            return str(literal.data['value'])
        elif literal.data['value_type'] == TokenType.FLOAT_LITERAL:
            return str(literal.data['value'])
        elif literal.data['value_type'] == TokenType.STRING:
            return f"'{literal.data['value']}'"
        elif literal.data['value_type'] == TokenType.NULL:
            return "NULL"
        else:
            raise ValueError(f"Unsupported literal type: {literal.data['value_type']}")

    def generate_insert(self, ast: ASTNode) -> str:
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

    def generate_update(self, ast: ASTNode) -> str:
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

    def generate_delete(self, ast: ASTNode) -> str:
        sql = "DELETE FROM "
        sql += self.generate_table_reference(ast.data['table'])

        if ast.data['where_clause']:
            sql += " WHERE "
            sql += self.generate_condition(ast.data['where_clause'])

        return sql

    def generate_create(self, ast: ASTNode) -> str:
        sql = "CREATE TABLE "
        sql += self.generate_table_reference(ast.data['table'])

        sql += " ("
        column_strs = []
        for column in ast.data['columns']:
            column_strs.append(self.generate_column_definition(column))
        sql += ", ".join(column_strs)
        sql += ")"

        return sql

    def generate_column_definition(self, column: ASTNode) -> str:
        # Ensure we get the string name from the IDENTIFIER ASTNode
        if column.data['name'].type == NodeType.IDENTIFIER:
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

    def generate_drop(self, ast: ASTNode) -> str:
        sql = "DROP TABLE "
        sql += self.generate_table_reference(ast.data['table'])
        return sql

    def token_type_to_string(self, token_type: TokenType) -> str:
        token_strings = {
            TokenType.SELECT: "SELECT",
            TokenType.FROM: "FROM",
            TokenType.WHERE: "WHERE",
            TokenType.INSERT: "INSERT",
            TokenType.INTO: "INTO",
            TokenType.VALUES: "VALUES",
            TokenType.UPDATE: "UPDATE",
            TokenType.SET: "SET",
            TokenType.DELETE: "DELETE",
            TokenType.CREATE: "CREATE",
            TokenType.TABLE: "TABLE",
            TokenType.DROP: "DROP",
            TokenType.JOIN: "JOIN",
            TokenType.ON: "ON",
            TokenType.AND: "AND",
            TokenType.OR: "OR",
            TokenType.NOT: "NOT",
            TokenType.NULL: "NULL",
            TokenType.INT: "INT",
            TokenType.TEXT: "TEXT",
            TokenType.FLOAT: "FLOAT",
            TokenType.DATE: "DATE",
            TokenType.EQUALS: "=",
            TokenType.GREATER: ">",
            TokenType.LESS: "<",
            TokenType.GREATER_EQUALS: ">=",
            TokenType.LESS_EQUALS: "<=",
            TokenType.NOT_EQUALS: "!=",
            TokenType.PLUS: "+",
            TokenType.MINUS: "-",
            TokenType.ASTERISK: "*",
            TokenType.DIVIDE: "/",
            TokenType.COMMA: ",",
            TokenType.SEMICOLON: ";",
            TokenType.LEFT_PAREN: "(",
            TokenType.RIGHT_PAREN: ")",
            TokenType.DOT: "."
        }

        return token_strings.get(token_type, str(token_type))
