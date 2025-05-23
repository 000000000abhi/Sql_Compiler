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
