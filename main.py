#!/usr/bin/env python3
import tkinter as tk
from ui import SQLCompilerUI

def main():
    root = tk.Tk()
    app = SQLCompilerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
