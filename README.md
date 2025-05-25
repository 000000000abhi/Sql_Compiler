# TempSQL – A Lightweight SQL Compiler and GUI

**TempSQL** is a lightweight SQL compiler built in Python. It supports lexing, parsing, and executing SQL queries against an in-memory database. The project includes a GUI for executing queries and viewing results, aimed at educational or small-scale development use.

## Features

- SQL Lexer and Parser  
- AST-based SQL Compiler  
- In-memory database execution engine  
- Tkinter GUI for query input and result display  
- Basic SQL support for `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, and `DROP`  
- Command history and syntax error display  
- Test framework for compiler and database engine  

## Project Structure

```
tempsql/
│
├── database.py         # In-memory database implementation
├── lexer.py            # SQL lexer
├── lexer_test.py       # Lexer unit tests
├── main.py             # CLI entry point
├── run_test.py         # Script to run all tests
├── sql_compiler.py     # AST-based SQL compiler
├── test_sql.py         # Unit tests for SQL compilation
├── ui.py               # Tkinter GUI application
├── README.md           # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.8+
- No external dependencies (uses standard library only)

### Run the GUI

```bash
python tempsql/ui.py
```

### Run from CLI

```bash
python tempsql/main.py
```

### Run All Tests

```bash
python tempsql/run_test.py
```

## Example Queries

```
CREATE TABLE students (id INT, name TEXT);
INSERT INTO students VALUES (1, 'Alice');
SELECT * FROM students;
```

## Notes

- SQL parsing is done via a custom lexer and compiler—no third-party SQL engines are used.  
- GUI supports query execution and shows results or error messages.  
- This project is intended for learning, prototyping, or small-scale demos.  

## License

This project is provided as-is for educational purposes. Add a license file if open-sourcing.
