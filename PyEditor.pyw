import tkinter as tk
from tkinter import filedialog, messagebox
import idlelib.colorizer as idc
import idlelib.percolator as idp
import subprocess
import re
import chardet  # 用于检测文件编码
import Python
import Python.Scripts
import os

class CodeEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Editor")
        self.root.geometry("800x600")

        # 创建菜单栏
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        # 创建文件菜单
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        # 创建运行菜单
        self.run_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Run", menu=self.run_menu)
        self.run_menu.add_command(label="Run Code", command=self.run_code, accelerator="F5")
        self.root.bind("<F5>", lambda event: self.run_code())

        # 创建代码编辑区
        self.code_area = tk.Text(self.root, font=("Consolas", 12), bg="#282c34", fg="#abb2bf", insertbackground="#abb2bf")
        self.code_area.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        self.code_area.bind("<Tab>", self.tab_to_spaces)
        self.code_area.bind("<Return>", self.auto_indent)
        self.code_area.bind("<BackSpace>", self.smart_backspace)

        # 配置语法高亮
        self.configure_syntax_highlighting()

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Python Files", "*.py"),
                ("Python Windows Files", "*.pyw"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            try:
                # 检测文件编码
                with open(file_path, 'rb') as file:
                    raw_data = file.read()
                detected_encoding = chardet.detect(raw_data)['encoding']
                # 读取文件内容
                with open(file_path, 'r', encoding=detected_encoding) as file:
                    content = file.read()
                self.code_area.delete(1.0, tk.END)
                self.code_area.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def save_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Save File",
            filetypes=[
                ("Python Files", "*.py"),
                ("Python Windows Files", "*.pyw"),
                ("All files", "*.*")
            ],
            defaultextension=".py"
        )
        if file_path:
            try:
                # 保存文件内容
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.code_area.get(1.0, tk.END))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def run_code(self):
        code = self.code_area.get(1.0, tk.END)
        # 将代码保存到临时文件
        with open("temp_code.py", "w", encoding="utf-8") as file:
            file.write(code)
        # 使用 Python 文件夹中的 Python 解释器运行当前脚本
        python_path = os.path.join(os.path.dirname(__file__), "Python", "Scripts", "python.exe")
        script_path = os.path.join(os.path.dirname(__file__), "temp_code.py")
        try:
            subprocess.run([python_path, script_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run code: {e}")

    def tab_to_spaces(self, event):
        self.code_area.insert(tk.INSERT, "    ")
        return "break"

    def auto_indent(self, event):
        line = self.code_area.get("insert linestart", "insert lineend")
        match = re.match(r'^(\s+)', line)
        current_indent = len(match.group(0)) if match else 0
        if line.strip().endswith(":"):
            new_indent = current_indent + 4
        else:
            new_indent = current_indent
        self.code_area.insert("insert", "\n" + " " * new_indent)
        return "break"

    def smart_backspace(self, event):
        line_start = self.code_area.index("insert linestart")
        line_end = self.code_area.index("insert")
        line_content = self.code_area.get(line_start, line_end)
        if line_content.strip() == "":
            space_count = len(line_content)
            remainder = space_count % 4
            if remainder != 0:
                delete_count = remainder
            else:
                delete_count = 4
            self.code_area.delete(line_start, f"{line_start}+{delete_count}c")
            return "break"
        else:
            return

    def configure_syntax_highlighting(self):
        p = idp.Percolator(self.code_area)
        d = idc.ColorDelegator()
        p.insertfilter(d)

        theme = {
            "KEYWORD": {"foreground": "#c678dd", "background": "#282c34"},
            "BUILTIN": {"foreground": "#56b6c2", "background": "#282c34"},
            "COMMENT": {"foreground": "#5c6370", "background": "#282c34"},
            "STRING": {"foreground": "#98c379", "background": "#282c34"},
            "DEFINITION": {"foreground": "#61afef", "background": "#282c34"},
            "CLASS": {"foreground": "#e06c75", "background": "#282c34"},
        }

        for tag, config in theme.items():
            self.code_area.tag_config(tag, **config)

if __name__ == "__main__":
    root = tk.Tk()
    editor = CodeEditor(root)
    root.mainloop()