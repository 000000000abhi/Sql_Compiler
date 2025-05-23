import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import sys
import os
import json
import re
from datetime import datetime
import tempfile
import threading
import time

# Add the current directory to the path to import the SQL compiler modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sql_compiler import SQLGenerator
    from database import Database
except ImportError as e:
    print(f"Error importing SQL compiler modules: {e}")
    sys.exit(1)

class SQLCompilerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SQL Compiler")
        self.root.geometry("1000x700")
        
        # Set application icon (if available)
        try:
            self.root.iconbitmap("sql_icon.ico")  # Replace with your icon path
        except:
            pass  # Icon not found, continue without it
        
        # Initialize database and compiler
        self.db = Database()
        self.compiler = SQLGenerator(self.db)
        
        # Get database schema for validation
        try:
            self.schema = self.db.get_schema()
        except:
            self.schema = {}  # Empty schema if not available
            
        # Query history
        self.history = []
        
        # Error checking timer
        self.error_check_timer = None
        self.last_typed = 0
        self.error_delay = 1000  # ms delay before checking errors
        
        # Create the UI components
        self.create_menu()
        self.create_ui()
        
        # Set theme colors
        self.set_theme()
        
        # Start error checking thread
        self.start_error_checking()

    def set_theme(self):
        # Configure ttk styles with a modern look
        style = ttk.Style()
        
        # Define colors with more vibrant options
        primary_color = "#6366F1"  # Brighter indigo
        secondary_color = "#4F46E5"  # Slightly darker indigo
        success_color = "#10B981"  # Emerald green
        error_color = "#EF4444"  # Red
        warning_color = "#F59E0B"  # Amber
        background_color = "#F9FAFB"  # Light gray
        text_color = "#1F2937"  # Dark gray
        border_color = "#E5E7EB"  # Light border
        accent_color = "#8B5CF6"  # Purple accent
        
        # Configure general styles
        style.configure(".", font=('Segoe UI', 10))
        style.configure("TFrame", background=background_color)
        style.configure("TLabel", background=background_color, foreground=text_color)
        
        # Modern button styling with better text visibility
        style.configure("TButton", 
                       padding=(12, 8), 
                       relief="flat", 
                       background=primary_color, 
                       foreground="white", 
                       font=('Segoe UI', 10, 'bold'))
        style.map("TButton", 
                 background=[('pressed', secondary_color), ('active', primary_color)],
                 foreground=[('pressed', 'white'), ('active', 'white')])
        
        # Add custom button style with rounded corners and shadow effect
        self.root.tk.call('namespace', 'import', 'ttk::*') if hasattr(self.root, 'tk') else None
        self.root.tk.call('source', 'azure.tcl') if hasattr(self.root, 'tk') and os.path.exists('azure.tcl') else None
        
        # Configure specific button styles with better contrast
        style.configure("Execute.TButton", 
                       background=success_color, 
                       foreground="white", 
                       font=('Segoe UI', 10, 'bold'))
        style.map("Execute.TButton", 
                 background=[('pressed', '#059669'), ('active', '#34D399')],
                 foreground=[('pressed', 'white'), ('active', 'white')])
        
        style.configure("Clear.TButton", 
                       background="#6B7280", 
                       foreground="white",
                       font=('Segoe UI', 10, 'bold'))
        style.map("Clear.TButton", 
                 background=[('pressed', '#4B5563'), ('active', '#9CA3AF')],
                 foreground=[('pressed', 'white'), ('active', 'white')])
        
        # Add card-like styling to main containers
        style.configure("Card.TFrame", 
                       background="white", 
                       relief="solid", 
                       borderwidth=1)
        
        # Configure notebook styles with more modern appearance
        style.configure("TNotebook", 
                       background=background_color, 
                       tabmargin=0)
        style.configure("TNotebook.Tab", 
                       padding=[16, 8], 
                       font=('Segoe UI', 10, 'bold'), 
                       background="#E5E7EB", 
                       foreground=text_color)
        style.map("TNotebook.Tab", 
                 background=[('selected', primary_color)],
                 foreground=[('selected', 'white')])
        
        # Configure treeview (results table)
        style.configure("Treeview", 
                       background="white", 
                       foreground=text_color, 
                       rowheight=30,
                       fieldbackground="white",
                       borderwidth=1,
                       relief="solid")
        style.configure("Treeview.Heading", 
                       font=('Segoe UI', 10, 'bold'), 
                       background=primary_color, 
                       foreground="white",
                       relief="flat")
        style.map("Treeview", 
                 background=[('selected', '#EEF2FF')],
                 foreground=[('selected', primary_color)])
        
        # Configure LabelFrame
        style.configure("TLabelframe", background=background_color, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=background_color, foreground=primary_color, font=('Segoe UI', 11, 'bold'))
        
        # Configure Scrollbar
        style.configure("TScrollbar", background=background_color, bordercolor=border_color, 
                       arrowcolor=primary_color, troughcolor=background_color)

    def create_custom_button(self, parent, text, command, style=None, width=None):
        """Create a modern-looking button with guaranteed visibility"""
        if style == "Execute.TButton":
            bg_color = "#10B981"  # Success color
            hover_color = "#34D399"
            text_color = "white"
        elif style == "Clear.TButton":
            bg_color = "#6B7280"  # Gray
            hover_color = "#9CA3AF"
            text_color = "white"
        else:
            bg_color = "#6366F1"  # Primary color
            hover_color = "#818CF8"
            text_color = "white"
        
        # Create a frame with a colored background to act as button with border
        button_frame = tk.Frame(
            parent,
            background=bg_color,
            highlightbackground=hover_color,
            highlightthickness=1,
            bd=0
        )
        
        # Add padding around the button
        if width:
            button = tk.Label(
                button_frame,
                text=text,
                bg=bg_color,
                fg=text_color,
                font=('Segoe UI', 10, 'bold'),
                padx=15,
                pady=8,
                width=width,
                cursor="hand2"
            )
        else:
            button = tk.Label(
                button_frame,
                text=text,
                bg=bg_color,
                fg=text_color,
                font=('Segoe UI', 10, 'bold'),
                padx=15,
                pady=8,
                cursor="hand2"
            )
        
        button.pack(fill=tk.BOTH, expand=True)
        
        # Bind events to both the frame and label
        button.bind("<Button-1>", lambda e: command())
        button_frame.bind("<Button-1>", lambda e: command())
        
        # Add hover effect
        def on_enter(e):
            button_frame.config(background=hover_color)
            button.config(background=hover_color)
        
        def on_leave(e):
            button_frame.config(background=bg_color)
            button.config(background=bg_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button_frame.bind("<Enter>", on_enter)
        button_frame.bind("<Leave>", on_leave)
        
        return button_frame

    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Query", command=self.new_query, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Query...", command=self.open_query, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Query...", command=self.save_query, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Clear Editor", command=self.clear_editor)
        edit_menu.add_command(label="Format SQL", command=self.format_sql)
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy", command=self.copy_text, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste_text, accelerator="Ctrl+V")
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Show Schema", command=self.show_schema)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="SQL Help", command=self.show_sql_help)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda event: self.new_query())
        self.root.bind("<Control-o>", lambda event: self.open_query())
        self.root.bind("<Control-s>", lambda event: self.save_query())

    def create_ui(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="16")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and description with improved styling
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 16))
        
        title_label = ttk.Label(
            title_frame, 
            text="SQL Compiler", 
            font=("Segoe UI", 24, "bold"),
            foreground="#6366F1"  # Primary indigo color
        )
        title_label.pack(side=tk.LEFT, pady=(0, 5))
        
        description_label = ttk.Label(
            title_frame,
            text="Write and execute SQL queries with real-time error detection.",
            font=("Segoe UI", 12),
            foreground="#6B7280"  # Gray text for description
        )
        description_label.pack(side=tk.LEFT, padx=(16, 0), pady=(8, 0))
        
    # Replace the button creation section in create_ui with this code:
    
        # Button frame with improved styling
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Always use custom buttons for guaranteed visibility
        execute_button = self.create_custom_button(
            button_frame,
            text="Execute Query",
            command=self.execute_query,
            style="Execute.TButton"
        )
        execute_button.pack(side=tk.LEFT, padx=(0, 8))
        
        clear_button = self.create_custom_button(
            button_frame,
            text="Clear",
            command=self.clear_editor,
            style="Clear.TButton"
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 8))
        
        save_button = self.create_custom_button(
            button_frame,
            text="Save",
            command=self.save_query
        )
        save_button.pack(side=tk.LEFT, padx=(0, 8))
        
        load_button = self.create_custom_button(
            button_frame,
            text="Load",
            command=self.open_query
        )
        load_button.pack(side=tk.LEFT)
        
        # Schema button on the right
        schema_button = self.create_custom_button(
            button_frame,
            text="Show Schema",
            command=self.show_schema
        )
        schema_button.pack(side=tk.RIGHT)
        
        # Create a paned window for resizable sections
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        
        # Query editor frame with card-like styling
        editor_frame = ttk.LabelFrame(paned_window, text="SQL Query", style="Card.TFrame")
        paned_window.add(editor_frame, weight=40)
        
        # Add error message label above the editor
        self.error_label = ttk.Label(
            editor_frame,
            text="",
            foreground="#EF4444",  # Red for errors
            font=("Segoe UI", 10, "italic")
        )
        self.error_label.pack(fill=tk.X, padx=8, pady=(8, 0))
        
        # Editor with line numbers
        editor_container = ttk.Frame(editor_frame)
        editor_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Line numbers text widget
        self.line_numbers = tk.Text(
            editor_container,
            width=4,
            padx=5,
            pady=8,
            takefocus=0,
            border=0,
            background='#F3F4F6',
            foreground='#6B7280',
            font=("Cascadia Code", 12),
            state=tk.DISABLED
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Query editor with improved styling
        self.query_editor = scrolledtext.ScrolledText(
            editor_container,
            wrap=tk.WORD,
            width=40,
            height=10,
            font=("Cascadia Code", 12),
            background="white",
            foreground="#1F2937",
            insertbackground="#6366F1",
            selectbackground="#E0E7FF",
            selectforeground="#1F2937",
            padx=8,
            pady=8,
            borderwidth=0
        )
        self.query_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Default query
        self.query_editor.insert(tk.END, "SELECT * FROM users LIMIT 10;")
        
        # Configure tags for syntax highlighting
        self.query_editor.tag_configure("keyword", foreground="#6366F1", font=("Cascadia Code", 12, "bold"))
        self.query_editor.tag_configure("function", foreground="#9333EA", font=("Cascadia Code", 12))
        self.query_editor.tag_configure("string", foreground="#10B981")
        self.query_editor.tag_configure("number", foreground="#F59E0B")
        self.query_editor.tag_configure("comment", foreground="#9CA3AF", font=("Cascadia Code", 12, "italic"))
        self.query_editor.tag_configure("error", foreground="#EF4444", underline=True)
        self.query_editor.tag_configure("table", foreground="#3B82F6")
        self.query_editor.tag_configure("column", foreground="#F97316")
        
        # Bind events for syntax highlighting and error checking
        self.query_editor.bind("<KeyRelease>", self.on_key_release)
        self.query_editor.bind("<<Modified>>", self.update_line_numbers)
        self.query_editor.bind("<Configure>", self.update_line_numbers)
        
        # Results notebook (tabs) with improved styling
        self.results_notebook = ttk.Notebook(paned_window)
        paned_window.add(self.results_notebook, weight=60)
        
        # Results tab with card-like styling
        self.results_frame = ttk.Frame(self.results_notebook, style="Card.TFrame")
        self.results_notebook.add(self.results_frame, text="Results")
        
        # Create a frame for the results table
        self.table_frame = ttk.Frame(self.results_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Initial message with improved styling
        self.initial_message = ttk.Label(
            self.table_frame,
            text="Execute a query to see results",
            font=("Segoe UI", 14),
            foreground="#6B7280"
        )
        self.initial_message.pack(expand=True)
        
        # History tab with card-like styling
        self.history_frame = ttk.Frame(self.results_notebook, style="Card.TFrame")
        self.results_notebook.add(self.history_frame, text="History")
        
        # Create history list with improved styling
        history_container = ttk.Frame(self.history_frame)
        history_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        history_label = ttk.Label(
            history_container,
            text="Query History",
            font=("Segoe UI", 12, "bold"),
            foreground="#6366F1"
        )
        history_label.pack(side=tk.TOP, anchor=tk.W, pady=(0, 8))
        
        self.history_list = tk.Listbox(
            history_container,
            font=("Cascadia Code", 11),
            activestyle="none",
            selectbackground="#E0E7FF",
            selectforeground="#6366F1",
            background="white",
            foreground="#1F2937",
            borderwidth=1,
            relief=tk.SOLID,
            highlightthickness=0
        )
        self.history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for history list
        history_scrollbar = ttk.Scrollbar(history_container, orient=tk.VERTICAL, command=self.history_list.yview)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_list.config(yscrollcommand=history_scrollbar.set)
        
        # Bind double-click on history item
        self.history_list.bind("<Double-Button-1>", self.load_from_history)
        
        # Schema tab with card-like styling
        self.schema_frame = ttk.Frame(self.results_notebook, style="Card.TFrame")
        self.results_notebook.add(self.schema_frame, text="Schema")
        
        # Create schema tree view
        self.create_schema_view()
        
        # Status bar with improved styling
        status_frame = ttk.Frame(self.root, style="TFrame")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(8, 4),
            background="#F3F4F6",
            foreground="#4B5563"
        )
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add execution time display
        self.exec_time_var = tk.StringVar()
        exec_time_label = ttk.Label(
            status_frame,
            textvariable=self.exec_time_var,
            relief=tk.SUNKEN,
            padding=(8, 4),
            background="#F3F4F6",
            foreground="#4B5563"
        )
        exec_time_label.pack(side=tk.RIGHT, padx=(8, 0))
        
        # Initial line numbers update
        self.update_line_numbers()
        
        # Initial syntax highlighting
        self.highlight_syntax()
    def highlight_syntax(self, event=None):
        # Clear all tags
        for tag in ["keyword", "function", "string", "number", "comment", "error", "table", "column"]:
            self.query_editor.tag_remove(tag, "1.0", tk.END)
        
        # SQL keywords
        keywords = [
            "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "TABLE",
            "INTO", "VALUES", "SET", "AND", "OR", "NOT", "NULL", "IS", "IN", "LIKE", "BETWEEN",
            "JOIN", "INNER", "LEFT", "RIGHT", "OUTER", "ON", "GROUP", "BY", "HAVING", "ORDER",
            "ASC", "DESC", "LIMIT", "OFFSET", "UNION", "ALL", "DISTINCT", "AS", "CASE", "WHEN",
            "THEN", "ELSE", "END", "IF", "EXISTS", "PRIMARY", "KEY", "FOREIGN", "REFERENCES",
            "DEFAULT", "AUTO_INCREMENT", "UNIQUE", "INDEX", "CHECK", "CONSTRAINT"
        ]
        
        # SQL functions
        functions = [
            "COUNT", "SUM", "AVG", "MIN", "MAX", "COALESCE", "IFNULL", "NULLIF", "CAST",
            "CONVERT", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP", "DATE", "EXTRACT",
            "DATEADD", "DATEDIFF", "DATEPART", "DAY", "MONTH", "YEAR", "CONCAT", "SUBSTRING",
            "TRIM", "UPPER", "LOWER", "LENGTH", "ROUND", "CEIL", "FLOOR", "ABS", "RAND"
        ]
        
        # Get the text content
        content = self.query_editor.get("1.0", tk.END)
        
        # Highlight keywords
        for keyword in keywords:
            start_pos = "1.0"
            while True:
                start_pos = self.query_editor.search(
                    r'\y' + keyword + r'\y',
                    start_pos,
                    tk.END,
                    nocase=True,
                    regexp=True
                )
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(keyword)}c"
                self.query_editor.tag_add("keyword", start_pos, end_pos)
                start_pos = end_pos
        
        # Highlight functions
        for function in functions:
            start_pos = "1.0"
            while True:
                start_pos = self.query_editor.search(
                    r'\y' + function + r'\y',
                    start_pos,
                    tk.END,
                    nocase=True,
                    regexp=True
                )
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(function)}c"
                self.query_editor.tag_add("function", start_pos, end_pos)
                start_pos = end_pos
        
        # Highlight strings (single quotes)
        start_pos = "1.0"
        while True:
            start_pos = self.query_editor.search(
                r"'[^']*'",
                start_pos,
                tk.END,
                regexp=True
            )
            if not start_pos:
                break
            content_index = self.query_editor.index(start_pos)
            line, col = map(int, content_index.split('.'))
            text_line = self.query_editor.get(f"{line}.0", f"{line}.end")
            
            # Find the closing quote
            start_col = col
            in_string = False
            for i, char in enumerate(text_line[col:], col):
                if char == "'":
                    if not in_string:
                        in_string = True
                    else:
                        end_col = i + 1
                        self.query_editor.tag_add("string", f"{line}.{start_col}", f"{line}.{end_col}")
                        start_pos = f"{line}.{end_col}"
                        break
        
        # Highlight numbers
        start_pos = "1.0"
        while True:
            start_pos = self.query_editor.search(
                r'\y\d+(\.\d+)?\y',
                start_pos,
                tk.END,
                regexp=True
            )
            if not start_pos:
                break
            end_pos = self.query_editor.index(f"{start_pos} wordend")
            self.query_editor.tag_add("number", start_pos, end_pos)
            start_pos = end_pos
        
        # Highlight comments (-- and /* */)
        start_pos = "1.0"
        while True:
            start_pos = self.query_editor.search(
             r'--.*|/\*.*\*/',
             start_pos,
             tk.END,
             regexp=True
             )

            if not start_pos:
                break
            
            line, col = map(int, start_pos.split('.'))
            text_line = self.query_editor.get(f"{line}.0", f"{line}.end")
            
            # Single line comment
            if text_line[col:col+2] == '--':
                self.query_editor.tag_add("comment", start_pos, f"{line}.end")
                start_pos = f"{line+1}.0"
            
            # Multi-line comment
            elif text_line[col:col+2] == '/*':
                # Find the closing */
                end_pos = self.query_editor.search(
                    r'\*/',
                    start_pos,
                    tk.END
                )
                if end_pos:
                    end_pos = self.query_editor.index(f"{end_pos}+2c")
                    self.query_editor.tag_add("comment", start_pos, end_pos)
                    start_pos = end_pos
                else:
                    # No closing comment found, highlight to the end
                    self.query_editor.tag_add("comment", start_pos, tk.END)
                    break
            else:
                # Move to next line if pattern doesn't match expected comment syntax
                start_pos = f"{line+1}.0"
        
        # Highlight table names (if schema is available)
        if hasattr(self, 'schema') and self.schema:
            for table_name in self.schema.keys():
                start_pos = "1.0"
                while True:
                    start_pos = self.query_editor.search(
                        r'\y' + table_name + r'\y',
                        start_pos,
                        tk.END,
                        nocase=True,
                        regexp=True
                    )
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(table_name)}c"
                    
                    # Don't highlight if it's part of a keyword or already highlighted
                    if not self.query_editor.tag_names(start_pos):
                        self.query_editor.tag_add("table", start_pos, end_pos)
                    
                    start_pos = end_pos
            
            # Highlight column names
            for table_name, columns in self.schema.items():
                for column_info in columns:
                    column_name = column_info.get('name')
                    if column_name:
                        start_pos = "1.0"
                        while True:
                            start_pos = self.query_editor.search(
                                r'\y' + column_name + r'\y',
                                start_pos,
                                tk.END,
                                nocase=True,
                                regexp=True
                            )
                            if not start_pos:
                                break
                            end_pos = f"{start_pos}+{len(column_name)}c"
                            
                            # Don't highlight if it's part of a keyword or already highlighted
                            if not self.query_editor.tag_names(start_pos):
                                self.query_editor.tag_add("column", start_pos, end_pos)
                            
                            start_pos = end_pos

    def create_schema_view(self):
        """Create the schema view with improved error handling"""
        # Create container for schema view
        schema_container = ttk.Frame(self.schema_frame)
        schema_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Add header
        schema_header = ttk.Frame(schema_container)
        schema_header.pack(fill=tk.X, pady=(0, 8))
        
        schema_title = ttk.Label(
            schema_header,
            text="Database Schema",
            font=("Segoe UI", 12, "bold"),
            foreground="#6366F1"
        )
        schema_title.pack(side=tk.LEFT)
        
        # Always use custom button for refresh
        refresh_button = self.create_custom_button(
            schema_header,
            text="Refresh",
            command=self.populate_schema_tree
        )
        refresh_button.pack(side=tk.RIGHT)
        
        # Create treeview for schema
        self.schema_tree = ttk.Treeview(schema_container, style="Treeview")
        self.schema_tree.heading('#0', text='Database Schema', anchor=tk.W)
        self.schema_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        schema_scrollbar = ttk.Scrollbar(schema_container, orient=tk.VERTICAL, command=self.schema_tree.yview)
        schema_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.schema_tree.config(yscrollcommand=schema_scrollbar.set)
        
        # Add status message area
        self.schema_status = ttk.Label(
            schema_container,
            text="",
            font=("Segoe UI", 10, "italic"),
            foreground="#6B7280"
        )
        self.schema_status.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 0))
        
        # Populate schema tree
        self.populate_schema_tree()

    def populate_schema_tree(self):
        """Populate the schema tree with database structure"""
        # Clear existing items
        for item in self.schema_tree.get_children():
            self.schema_tree.delete(item)
        
        # Try to get schema from database
        try:
            # If schema is empty or None, try to refresh it
            if not hasattr(self, 'schema') or not self.schema:
                self.schema = self.db.get_schema()
            
            # Check if schema is still empty after refresh
            if not self.schema:
                # Add a message if schema is empty
                self.schema_tree.insert('', 'end', text="No schema information available", tags=('message',))
                self.schema_tree.tag_configure('message', foreground='#6B7280', font=('Segoe UI', 11, 'italic'))
                return
                
            # Add tables to tree
            for table_name, columns in self.schema.items():
                table_node = self.schema_tree.insert('', 'end', text=table_name, open=False, 
                                                    tags=('table',))
                
                # Add columns to table
                for column in columns:
                    column_name = column.get('name', 'Unknown')
                    column_type = column.get('type', 'Unknown')
                    constraints = column.get('constraints', [])
                    
                    # Format constraints
                    constraints_str = ', '.join(constraints) if constraints else ''
                    
                    # Create display text
                    display_text = f"{column_name} ({column_type})"
                    if constraints_str:
                        display_text += f" [{constraints_str}]"
                    
                    self.schema_tree.insert(table_node, 'end', text=display_text, tags=('column',))
            
            # Configure tag appearance
            self.schema_tree.tag_configure('table', foreground='#6366F1', font=('Segoe UI', 11, 'bold'))
            self.schema_tree.tag_configure('column', foreground='#1F2937')
            
        except Exception as e:
            # Show error if schema can't be loaded
            error_node = self.schema_tree.insert('', 'end', text="Error loading schema", tags=('error',))
            self.schema_tree.insert(error_node, 'end', text=str(e), tags=('error',))
            self.schema_tree.tag_configure('error', foreground='#EF4444')
            
            # Log the error to console for debugging
            print(f"Schema loading error: {str(e)}")

    def on_key_release(self, event=None):
        # Update line numbers
        self.update_line_numbers()
        
        # Perform syntax highlighting
        self.highlight_syntax()
        
        # Schedule error checking after a delay
        self.last_typed = time.time()
        if self.error_check_timer:
            self.root.after_cancel(self.error_check_timer)
        self.error_check_timer = self.root.after(self.error_delay, self.check_query_errors)

    def update_line_numbers(self, event=None):
        # Enable editing of line numbers
        self.line_numbers.config(state=tk.NORMAL)
        
        # Clear line numbers
        self.line_numbers.delete('1.0', tk.END)
        
        # Get total lines
        total_lines = self.query_editor.get('1.0', tk.END).count('\n')
        
        # Add line numbers
        for i in range(1, total_lines + 1):
            self.line_numbers.insert(tk.END, f"{i}\n")
        
        # Disable editing of line numbers
        self.line_numbers.config(state=tk.DISABLED)
     
    def check_query_errors(self):
        """Check for errors in the SQL query in real-time"""
        query = self.query_editor.get("1.0", tk.END).strip()
        if not query:
            self.error_label.config(text="")
            return
        
        # Clear previous error tags
        self.query_editor.tag_remove("error", "1.0", tk.END)
        
        # Basic syntax validation
        errors = []
        
        # Check for unbalanced quotes
        single_quotes = query.count("'")
        if single_quotes % 2 != 0:
            errors.append("Unbalanced single quotes")
            
            # Highlight unbalanced quotes
            in_quote = False
            last_quote_pos = None
            
            for i, char in enumerate(query):
                if char == "'":
                    in_quote = not in_quote
                    last_quote_pos = i
            
            if last_quote_pos is not None:
                # Find the position in the text widget
                line_count = query[:last_quote_pos].count('\n')
                if line_count > 0:
                    last_line_start = query[:last_quote_pos].rindex('\n') + 1
                    col = last_quote_pos - last_line_start
                else:
                    col = last_quote_pos
                
                pos = f"{line_count + 1}.{col}"
                self.query_editor.tag_add("error", pos, f"{pos}+1c")
        
        # Check for unbalanced parentheses
        open_parens = query.count("(")
        close_parens = query.count(")")
        if open_parens != close_parens:
            errors.append(f"Unbalanced parentheses: {open_parens} opening vs {close_parens} closing")
            
            # Highlight unbalanced parentheses
            stack = []
            for i, char in enumerate(query):
                if char == '(':
                    stack.append(i)
                elif char == ')':
                    if stack:
                        stack.pop()
                    else:
                        # Extra closing parenthesis
                        line_count = query[:i].count('\n')
                        if line_count > 0:
                            last_line_start = query[:i].rindex('\n') + 1
                            col = i - last_line_start
                        else:
                            col = i
                        
                        pos = f"{line_count + 1}.{col}"
                        self.query_editor.tag_add("error", pos, f"{pos}+1c")
            
            # Highlight unclosed opening parentheses
            for pos in stack:
                line_count = query[:pos].count('\n')
                if line_count > 0:
                    last_line_start = query[:pos].rindex('\n') + 1
                    col = pos - last_line_start
                else:
                    col = pos
                
                pos = f"{line_count + 1}.{col}"
                self.query_editor.tag_add("error", pos, f"{pos}+1c")
        
        # Check for missing semicolons at the end
        if not query.rstrip().endswith(';'):
            errors.append("Query should end with a semicolon")
        
        # Schema validation (if available)
        if hasattr(self, 'schema') and self.schema:
            # Extract table names from query
            table_pattern = r'FROM\s+([a-zA-Z0-9_]+)|JOIN\s+([a-zA-Z0-9_]+)|UPDATE\s+([a-zA-Z0-9_]+)|INSERT\s+INTO\s+([a-zA-Z0-9_]+)|DELETE\s+FROM\s+([a-zA-Z0-9_]+)'
            tables_in_query = []
            
            for match in re.finditer(table_pattern, query, re.IGNORECASE):
                table_name = next((g for g in match.groups() if g), None)
                if table_name and table_name.lower() not in [t.lower() for t in tables_in_query]:
                    tables_in_query.append(table_name)
            
            # Check if tables exist in schema
            for table in tables_in_query:
                if not any(table.lower() == t.lower() for t in self.schema.keys()):
                    errors.append(f"Table '{table}' does not exist in the database")
                    
                    # Highlight the unknown table
                    start_pos = "1.0"
                    while True:
                        start_pos = self.query_editor.search(
                            r'\y' + table + r'\y',
                            start_pos,
                            tk.END,
                            nocase=True,
                            regexp=True
                        )
                        if not start_pos:
                            break
                        end_pos = f"{start_pos}+{len(table)}c"
                        self.query_editor.tag_add("error", start_pos, end_pos)
                        start_pos = end_pos
            
            # Extract column references
            column_pattern = r'SELECT\s+(.*?)\s+FROM|WHERE\s+(.*?)(?:\s+(?:AND|OR|GROUP|ORDER|LIMIT|$))|ORDER\s+BY\s+(.*?)(?:\s+(?:ASC|DESC|LIMIT|$))|GROUP\s+BY\s+(.*?)(?:\s+(?:HAVING|ORDER|LIMIT|$))'
            column_sections = []
            
            for match in re.finditer(column_pattern, query, re.IGNORECASE):
                section = next((g for g in match.groups() if g), None)
                if section:
                    column_sections.append(section)
            
            # Parse column names from sections
            for section in column_sections:
                # Skip * wildcard
                if '*' in section:
                    continue
                
                # Split by commas for multiple columns
                for column_expr in section.split(','):
                    # Extract simple column names (ignoring functions, aliases, etc.)
                    column_match = re.search(r'([a-zA-Z0-9_]+)(?:\.[a-zA-Z0-9_]+)?', column_expr.strip())
                    if column_match:
                        column_name = column_match.group(1)
                        
                        # Check if column exists in any table
                        column_exists = False
                        for table_columns in self.schema.values():
                            if any(column_name.lower() == col.get('name', '').lower() for col in table_columns):
                                column_exists = True
                                break
                        
                        if not column_exists and column_name.lower() not in ['count', 'sum', 'avg', 'min', 'max']:
                            # Highlight the unknown column
                            start_pos = "1.0"
                            while True:
                                start_pos = self.query_editor.search(
                                    r'\y' + column_name + r'\y',
                                    start_pos,
                                    tk.END,
                                    nocase=True,
                                    regexp=True
                                )
                                if not start_pos:
                                    break
                                end_pos = f"{start_pos}+{len(column_name)}c"
                                
                                # Check if it's not already tagged as a keyword or function
                                if not any(tag in self.query_editor.tag_names(start_pos) for tag in ['keyword', 'function']):
                                    self.query_editor.tag_add("error", start_pos, end_pos)
                                
                                start_pos = end_pos
        
        # Update error label
        if errors:
            self.error_label.config(text=errors[0])
        else:
            self.error_label.config(text="")

    def execute_query(self):
        query = self.query_editor.get("1.0", tk.END).strip()
        if not query:
            messagebox.showwarning("Empty Query", "Please enter a SQL query to execute.")
            return
        
        # Update status
        self.status_var.set("Executing query...")
        self.root.update_idletasks()
        
        # Record start time
        start_time = time.time()
        
        try:
            # Execute the query without using a cursor
            result = self.compiler.execute_without_cursor(query)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            self.exec_time_var.set(f"Execution time: {execution_time:.3f}s")
            
            # Add to history
            timestamp = datetime.now().strftime("%H:%M:%S")
            history_item = f"[{timestamp}] {query[:50]}{'...' if len(query) > 50 else ''}"
            self.history.append({"query": query, "timestamp": timestamp})
            self.history_list.insert(0, history_item)
            
            # Display results
            self.display_results(result)
            
            # Update status
            self.status_var.set(f"Query executed successfully at {timestamp}")
            
        except Exception as e:
            # Calculate execution time even for errors
            execution_time = time.time() - start_time
            self.exec_time_var.set(f"Execution time: {execution_time:.3f}s")
            
            # Show error message
            self.display_error(str(e))
            self.status_var.set(f"Error: {str(e)}")

    def display_results(self, result):
        # Clear previous results
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        # Switch to results tab
        self.results_notebook.select(0)
        
        # Check result type
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], list):
            # SELECT query result (columns, rows)
            columns, rows = result
            
            # Check if there are columns and rows to display
            if columns and rows is not None:
                # Create container for table and controls
                results_container = ttk.Frame(self.table_frame)
                results_container.pack(fill=tk.BOTH, expand=True)
                
                # Add controls above the table
                controls_frame = ttk.Frame(results_container)
                controls_frame.pack(fill=tk.X, pady=(0, 8))
                
                # Add export button
                try:
                    export_button = ttk.Button(
                        controls_frame,
                        text="Export Results",
                        command=lambda: self.export_results(columns, rows)
                    )
                except:
                    export_button = self.create_custom_button(
                        controls_frame,
                        text="Export Results",
                        command=lambda: self.export_results(columns, rows)
                    )
                export_button.pack(side=tk.LEFT)
                
                # Add row count label
                count_label = ttk.Label(
                    controls_frame,
                    text=f"Showing {len(rows)} rows",
                    font=("Segoe UI", 10),
                    foreground="#6B7280"
                )
                count_label.pack(side=tk.RIGHT, padx=8)
                
                # Create table container
                table_container = ttk.Frame(results_container)
                table_container.pack(fill=tk.BOTH, expand=True)
                
                # Create treeview for results
                tree = ttk.Treeview(table_container, columns=columns, show="headings", style="Treeview")
                
                # Configure columns
                for col in columns:
                    tree.heading(col, text=col)
                    # Adjust column width based on content or set a default
                    tree.column(col, width=120, anchor=tk.CENTER)
                
                # Add data
                for row in rows:
                    # Ensure row values are strings for display in Treeview
                    tree.insert("", tk.END, values=[str(value) if value is not None else "NULL" for value in row])
                
                # Add scrollbars
                x_scrollbar = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=tree.xview)
                y_scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=tree.yview)
                tree.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
                
                # Pack everything
                tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
                y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
            else:
                # Display a message if no data is returned for SELECT
                message_frame = ttk.Frame(self.table_frame, padding=20)
                message_frame.pack(fill=tk.BOTH, expand=True)
                
                # Add an info icon
                info_label = ttk.Label(
                    message_frame,
                    text="ℹ️",
                    font=("Segoe UI", 36),
                    foreground="#6366F1"
                )
                info_label.pack(pady=(0, 16))
                
                message_label = ttk.Label(
                    message_frame,
                    text="Query executed successfully. No rows found.",
                    font=("Segoe UI", 14),
                    foreground="#6B7280"
                )
                message_label.pack()
                
        elif isinstance(result, bool):
            # DML/DDL query result (True for success, False for failure)
            message_frame = ttk.Frame(self.table_frame, padding=20)
            message_frame.pack(fill=tk.BOTH, expand=True)
            
            # Success or failure icon
            icon_text = "✓" if result else "✗"
            icon_color = "#10B981" if result else "#EF4444"
            
            icon_label = ttk.Label(
                message_frame,
                text=icon_text,
                font=("Segoe UI", 64),
                foreground=icon_color
            )
            icon_label.pack(pady=(20, 16))
            
            # Message text
            message_text = "Query executed successfully." if result else "Query execution failed."
            message_label = ttk.Label(
                message_frame,
                text=message_text,
                font=("Segoe UI", 16),
                foreground=icon_color
            )
            message_label.pack()
            
        else:
            # Other result type (shouldn't typically happen with current execute_query)
            message_frame = ttk.Frame(self.table_frame, padding=20)
            message_frame.pack(fill=tk.BOTH, expand=True)
            
            message_label = ttk.Label(
                message_frame,
                text=f"Query executed successfully. Result: {result}",
                font=("Segoe UI", 14)
            )
            message_label.pack(expand=True)

    def display_error(self, error_message):
        # Clear previous results
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        # Switch to results tab
        self.results_notebook.select(0)
        
        # Create error frame with improved styling
        error_frame = ttk.Frame(self.table_frame, padding=20)
        error_frame.pack(fill=tk.BOTH, expand=True)
        
        # Error icon
        error_icon = ttk.Label(
            error_frame,
            text="⚠️",
            font=("Segoe UI", 64),
            foreground="#EF4444"
        )
        error_icon.pack(pady=(0, 16))
        
        # Error title
        error_title = ttk.Label(
            error_frame,
            text="SQL Error",
            font=("Segoe UI", 18, "bold"),
            foreground="#EF4444"
        )
        error_title.pack(pady=(0, 16))
        
        # Error message
        error_text = scrolledtext.ScrolledText(
            error_frame,
            wrap=tk.WORD,
            width=40,
            height=10,
            font=("Cascadia Code", 11),
            background="#FEF2F2",
            foreground="#B91C1C",
            borderwidth=1,
            relief=tk.SOLID
        )
        error_text.pack(fill=tk.BOTH, expand=True)
        error_text.insert(tk.END, error_message)
        error_text.config(state=tk.DISABLED)
        
        # Try to parse the error for better user guidance
        error_hint = self.get_error_hint(error_message)
        if error_hint:
            hint_frame = ttk.Frame(error_frame, padding=(0, 16, 0, 0))
            hint_frame.pack(fill=tk.X)
            
            hint_label = ttk.Label(
                hint_frame,
                text="💡 Hint:",
                font=("Segoe UI", 12, "bold"),
                foreground="#6B7280"
            )
            hint_label.pack(anchor=tk.W)
            
            hint_text = ttk.Label(
                hint_frame,
                text=error_hint,
                font=("Segoe UI", 11),
                foreground="#6B7280",
                wraplength=500,
                justify=tk.LEFT
            )
            hint_text.pack(anchor=tk.W, pady=(4, 0))

    def get_error_hint(self, error_message):
        """Provide helpful hints based on common SQL errors"""
        error_lower = error_message.lower()
        
        if "no such table" in error_lower:
            table_match = re.search(r"no such table:?\s+([a-zA-Z0-9_]+)", error_lower)
            if table_match:
                table_name = table_match.group(1)
                available_tables = list(self.schema.keys()) if hasattr(self, 'schema') and self.schema else []
                if available_tables:
                    return f"Table '{table_name}' doesn't exist. Available tables: {', '.join(available_tables)}"
                else:
                    return f"Table '{table_name}' doesn't exist. Check your table name."
        
        elif "syntax error" in error_lower:
            return "Check your SQL syntax. Common issues include missing commas between columns, unbalanced quotes, or incorrect keywords."
        
        elif "no such column" in error_lower:
            column_match = re.search(r"no such column:?\s+([a-zA-Z0-9_]+)", error_lower)
            if column_match:
                column_name = column_match.group(1)
                return f"Column '{column_name}' doesn't exist. Check your column names and make sure you're referencing the correct table."
        
        elif "constraint failed" in error_lower:
            return "A constraint (like PRIMARY KEY, FOREIGN KEY, UNIQUE, etc.) was violated by your operation."
        
        elif "near" in error_lower:
            near_match = re.search(r"near \"([^\"]+)\"", error_lower)
            if near_match:
                near_text = near_match.group(1)
                return f"Syntax error near '{near_text}'. Check this part of your query for mistakes."
        
        return None

    def export_results(self, columns, rows):
        """Export query results to a file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "w") as file:
                    # Write header
                    file.write(",".join([f'"{col}"' for col in columns]) + "\n")
                    
                    # Write data rows - FIXED VERSION
                    for row in rows:
                        csv_row = []
                        for val in row:
                            if val is None:
                                csv_row.append('""')
                            else:
                                # Properly escape quotes by doubling them and wrap in quotes
                                csv_row.append(f'"{str(val).replace("\"", "\"\"")}"')
                        file.write(",".join(csv_row) + "\n")
                    
                    self.status_var.set(f"Results exported to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export results: {str(e)}")

    def new_query(self):
        if messagebox.askyesno("New Query", "Clear the current query?"):
            self.query_editor.delete("1.0", tk.END)
            self.status_var.set("New query created")
            self.error_label.config(text="")

    def open_query(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".sql",
            filetypes=[("SQL files", "*.sql"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "r") as file:
                    content = file.read()
                    self.query_editor.delete("1.0", tk.END)
                    self.query_editor.insert(tk.END, content)
                    self.status_var.set(f"Loaded query from {os.path.basename(file_path)}")
                    self.highlight_syntax()
                    self.check_query_errors()
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")

    def save_query(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[("SQL files", "*.sql"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "w") as file:
                    content = self.query_editor.get("1.0", tk.END)
                    file.write(content)
                    self.status_var.set(f"Saved query to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {str(e)}")

    def clear_editor(self):
        if messagebox.askyesno("Clear Editor", "Clear the current query?"):
            self.query_editor.delete("1.0", tk.END)
            self.status_var.set("Editor cleared")
            self.error_label.config(text="")

    def load_from_history(self, event):
        selected_index = self.history_list.curselection()
        if selected_index:
            # Get the selected history item
            index = selected_index[0]
            if index < len(self.history):
                # Load the query into the editor
                self.query_editor.delete("1.0", tk.END)
                self.query_editor.insert(tk.END, self.history[index]["query"])
                self.highlight_syntax()
                self.check_query_errors()
                self.status_var.set(f"Loaded query from history ({self.history[index]['timestamp']})")

    def show_schema(self):
        """Show database schema and ensure it's properly displayed"""
        # Switch to schema tab
        self.results_notebook.select(2)
        
        # Force refresh schema data
        try:
            self.schema = self.db.get_schema()
        except Exception as e:
            # If there's an error getting the schema, show a message
            messagebox.showerror("Schema Error", f"Could not load schema: {str(e)}")
            
        # Populate the schema tree with the latest data
        self.populate_schema_tree()
        
        # Update status
        self.status_var.set("Schema refreshed")

    def format_sql(self):
        """Format the SQL query for better readability"""
        query = self.query_editor.get("1.0", tk.END).strip()
        if not query:
            return
        
        # Simple SQL formatter
        try:
            # Replace multiple spaces with a single space
            formatted = re.sub(r'\s+', ' ', query)
            
            # Format keywords
            keywords = [
                "SELECT", "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY", 
                "LIMIT", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", 
                "OUTER JOIN", "ON", "AND", "OR", "INSERT INTO", "VALUES", 
                "UPDATE", "SET", "DELETE FROM", "CREATE TABLE", "ALTER TABLE", 
                "DROP TABLE", "UNION", "UNION ALL"
            ]
            
            # Sort keywords by length (longest first) to avoid partial replacements
            keywords.sort(key=len, reverse=True)
            
            for keyword in keywords:
                # Replace keyword with newline + keyword
                pattern = r'(?i)\b' + keyword + r'\b'
                replacement = f"\n{keyword.upper()}"
                formatted = re.sub(pattern, replacement, formatted)
            
            # Add indentation
            lines = formatted.split('\n')
            indented_lines = []
            indent_level = 0
            
            for line in lines:
                if line.strip():
                    # Decrease indent for closing parentheses
                    if re.match(r'^\s*\)', line):
                        indent_level = max(0, indent_level - 1)
                    
                    # Add indentation
                    indented_lines.append('    ' * indent_level + line.strip())
                    
                    # Increase indent for opening parentheses
                    if line.strip().endswith('('):
                        indent_level += 1
            
            # Update editor with formatted SQL
            self.query_editor.delete("1.0", tk.END)
            self.query_editor.insert(tk.END, '\n'.join(indented_lines))
            self.highlight_syntax()
            self.status_var.set("SQL query formatted")
            
        except Exception as e:
            messagebox.showerror("Format Error", f"Could not format SQL: {str(e)}")

    def copy_text(self):
        """Copy selected text to clipboard"""
        try:
            selected_text = self.query_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            # No selection
            pass

    def paste_text(self):
        """Paste text from clipboard"""
        try:
            clipboard_text = self.root.clipboard_get()
            if self.query_editor.tag_ranges(tk.SEL):
                self.query_editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.query_editor.insert(tk.INSERT, clipboard_text)
            self.highlight_syntax()
        except tk.TclError:
            # Clipboard empty or not text
            pass

    def show_sql_help(self):
        """Show SQL help dialog"""
        help_window = tk.Toplevel(self.root)
        help_window.title("SQL Help")
        help_window.geometry("700x550")
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Create notebook for different help sections
        help_notebook = ttk.Notebook(help_window)
        help_notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # Basic syntax tab
        syntax_frame = ttk.Frame(help_notebook, padding=16)
        help_notebook.add(syntax_frame, text="Basic Syntax")
        
        syntax_title = ttk.Label(
            syntax_frame,
            text="SQL Basic Syntax",
            font=("Segoe UI", 16, "bold"),
            foreground="#6366F1"
        )
        syntax_title.pack(anchor=tk.W, pady=(0, 16))
        
        syntax_text = scrolledtext.ScrolledText(
            syntax_frame,
            wrap=tk.WORD,
            font=("Cascadia Code", 11),
            background="white",
            borderwidth=1,
            relief=tk.SOLID
        )
        syntax_text.pack(fill=tk.BOTH, expand=True)
        
        syntax_text.insert(tk.END, """
1. SELECT - Query data from a table
   SELECT column1, column2 FROM table_name WHERE condition;

2. INSERT - Add new data to a table
   INSERT INTO table_name (column1, column2) VALUES (value1, value2);

3. UPDATE - Modify existing data
   UPDATE table_name SET column1 = value1 WHERE condition;

4. DELETE - Remove data
   DELETE FROM table_name WHERE condition;

5. CREATE TABLE - Create a new table
   CREATE TABLE table_name (
       column1 datatype constraints,
       column2 datatype constraints
   );

6. DROP TABLE - Delete a table
   DROP TABLE table_name;

7. ALTER TABLE - Modify a table
   ALTER TABLE table_name ADD column_name datatype;
""")
        syntax_text.config(state=tk.DISABLED)
        
        # Examples tab
        examples_frame = ttk.Frame(help_notebook, padding=16)
        help_notebook.add(examples_frame, text="Examples")
        
        examples_title = ttk.Label(
            examples_frame,
            text="SQL Examples",
            font=("Segoe UI", 16, "bold"),
            foreground="#6366F1"
        )
        examples_title.pack(anchor=tk.W, pady=(0, 16))
        
        examples_text = scrolledtext.ScrolledText(
            examples_frame,
            wrap=tk.WORD,
            font=("Cascadia Code", 11),
            background="white",
            borderwidth=1,
            relief=tk.SOLID
        )
        examples_text.pack(fill=tk.BOTH, expand=True)
        
        examples_text.insert(tk.END, """
1. Select all columns from a table:
   SELECT * FROM users;

2. Select specific columns with a condition:
   SELECT username, email FROM users WHERE age > 18;

3. Join two tables:
   SELECT users.username, orders.order_date
   FROM users
   JOIN orders ON users.id = orders.user_id;

4. Group and aggregate data:
   SELECT category, COUNT(*) as count
   FROM products
   GROUP BY category
   HAVING count > 5;

5. Insert a new record:
   INSERT INTO users (username, email, age)
   VALUES ('john_doe', 'john@example.com', 25);

6. Update records:
   UPDATE products
   SET price = price * 1.1
   WHERE category = 'Electronics';

7. Delete records:
   DELETE FROM orders
   WHERE order_date < '2023-01-01';
""")
        examples_text.config(state=tk.DISABLED)
        
        # Keyboard shortcuts tab
        shortcuts_frame = ttk.Frame(help_notebook, padding=16)
        help_notebook.add(shortcuts_frame, text="Shortcuts")
        
        shortcuts_title = ttk.Label(
            shortcuts_frame,
            text="Keyboard Shortcuts",
            font=("Segoe UI", 16, "bold"),
            foreground="#6366F1"
        )
        shortcuts_title.pack(anchor=tk.W, pady=(0, 16))
        
        shortcuts_text = scrolledtext.ScrolledText(
            shortcuts_frame,
            wrap=tk.WORD,
            font=("Cascadia Code", 11),
            background="white",
            borderwidth=1,
            relief=tk.SOLID
        )
        shortcuts_text.pack(fill=tk.BOTH, expand=True)
        
        shortcuts_text.insert(tk.END, """
File Operations:
- Ctrl+N: New Query
- Ctrl+O: Open Query
- Ctrl+S: Save Query
- Alt+F4: Exit

Editing:
- Ctrl+C: Copy
- Ctrl+V: Paste
- Ctrl+Z: Undo
- Ctrl+Y: Redo

Execution:
- F5 or Ctrl+Enter: Execute Query

Navigation:
- Ctrl+Home: Go to beginning of document
- Ctrl+End: Go to end of document
- Ctrl+G: Go to line
""")
        shortcuts_text.config(state=tk.DISABLED)
        
        # Close button
        try:
            close_button = ttk.Button(
                help_window,
                text="Close",
                command=help_window.destroy,
                style="TButton"
            )
        except:
            close_button = self.create_custom_button(
                help_window,
                text="Close",
                command=help_window.destroy
            )
        close_button.pack(pady=16)

    def show_about(self):
        """Show about dialog with improved styling"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About SQL Compiler")
        about_window.geometry("500x400")
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Create frame with padding
        about_frame = ttk.Frame(about_window, padding=24)
        about_frame.pack(fill=tk.BOTH, expand=True)
        
        # App title
        title_label = ttk.Label(
            about_frame,
            text="SQL Compiler",
            font=("Segoe UI", 24, "bold"),
            foreground="#6366F1"
        )
        title_label.pack(pady=(0, 8))
        
        # Version
        version_label = ttk.Label(
            about_frame,
            text="Version 1.1.0",
            font=("Segoe UI", 12),
            foreground="#6B7280"
        )
        version_label.pack(pady=(0, 24))
        
        # Description
        description_text = scrolledtext.ScrolledText(
            about_frame,
            wrap=tk.WORD,
            width=40,
            height=8,
            font=("Segoe UI", 11),
            background="#F9FAFB",
            foreground="#1F2937",
            borderwidth=1,
            relief=tk.SOLID
        )
        description_text.pack(fill=tk.BOTH, expand=True)
        
        description_text.insert(tk.END, """
SQL Compiler is a powerful tool for writing, testing, and executing SQL queries with real-time error detection and syntax highlighting.

Features:
• Real-time SQL syntax highlighting
• Error detection while typing
• Query history tracking
• Database schema visualization
• Export query results
• SQL formatting
""")
        description_text.config(state=tk.DISABLED)
        
        # Copyright
        copyright_label = ttk.Label(
            about_frame,
            text="© 2023 Your Company",
            font=("Segoe UI", 10),
            foreground="#6B7280"
        )
        copyright_label.pack(pady=(24, 0))
        
        # Close button
        try:
            close_button = ttk.Button(
                about_frame,
                text="Close",
                command=about_window.destroy,
                style="TButton"
            )
        except:
            close_button = self.create_custom_button(
                about_frame,
                text="Close",
                command=about_window.destroy
            )
        close_button.pack(pady=(16, 0))

    def start_error_checking(self):
        """Start background thread for error checking"""
        def error_check_thread():
            while True:
                # Only check if enough time has passed since last keystroke
                current_time = time.time()
                if current_time - self.last_typed > (self.error_delay / 1000):
                    # Schedule error checking on the main thread
                    self.root.after(0, self.check_query_errors)
                
                # Sleep to avoid high CPU usage
                time.sleep(0.5)
        
        # Start the thread
        threading.Thread(target=error_check_thread, daemon=True).start()

# Main
if __name__ == "__main__":
    root = tk.Tk()
    app = SQLCompilerUI(root)
    root.mainloop()
