import sql_compiler as sc
from database import Database

def test_sql():
    # Create a database
    db = Database()
    
    # Test SQL statements
    sql_statements = [
        # Create a table
        "CREATE TABLE users (id INT, name TEXT, age INT, salary FLOAT);",
        
        # Insert data
        
        "INSERT INTO users (id, name, age, salary) VALUES (1, 'John', 30, 50000.0);",
        "INSERT INTO users (id, name, age, salary) VALUES (2, 'Jane', 25, 60000.0);",
        "INSERT INTO users (id, name, age, salary) VALUES (3, 'Bob', 40, 70000.0);",
        "INSERT INTO users (id, name, age, salary) VALUES (4, 'Abhijeet', 40, 70000.0);",
        
        # Select all users
        "SELECT * FROM users;",
        
        # Select specific columns
        "SELECT name, age FROM users;",
        
        # Select with condition
        "SELECT * FROM users WHERE age > 30;",
        
        # Update a user
        "UPDATE users SET salary = 55000.0 WHERE id = 1;",
        
        # Select after update
        "SELECT * FROM users;",
        
        # Delete a user
        "DELETE FROM users WHERE id = 2;",
        
        # Select after delete
        "SELECT * FROM users;",
        
        # Drop the table
        "DROP TABLE users;"
    ]
    
    # Execute each statement
    for sql in sql_statements:
        print(f"\nExecuting: {sql}")
        try:
            # Parse the SQL statement
            lexer = sc.Lexer(sql)
            parser = sc.Parser(lexer)
            ast = parser.parse()
            
            # Execute the query
            db.execute_query(ast)
            
            # Consume the semicolon if present
            if parser.current_token.type == sc.TokenType.SEMICOLON:
                parser.consume(sc.TokenType.SEMICOLON)
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_sql()
