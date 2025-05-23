from lexer import Lexer,TokenType 
def test_lexer(input_text: str):
    lexer = Lexer(input_text)
    
    # Loop to get and print each token until EOF
    while True:
        token = lexer.get_next_token()
        print(token)  
        if token.type == TokenType.EOF: 
            break

input_query = """
SELECT name, age FROM users WHERE age > 30;


"""

test_lexer(input_query)
