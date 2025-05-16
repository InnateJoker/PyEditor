import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import idlelib.colorizer as idc
import idlelib.percolator as idp
import subprocess
import re
import chardet
import threading
import queue

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

        # 创建输出显示区
        self.output_area = tk.Text(self.root, font=("Consolas", 12), bg="#3e4451", fg="#abb2bf")
        self.output_area.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)

        # 配置语法高亮
        self.configure_syntax_highlighting()

        # 创建一个队列用于线程间通信
        self.input_queue = queue.Queue()

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
        self.output_area.config(state="normal")
        self.output_area.delete(1.0, tk.END)
        self.output_area.config(state="disabled")

        # 创建一个临时文件保存代码
        with open("temp_code.py", "w", encoding="utf-8") as file:
            file.write(code)

        # 启动一个新线程来运行代码
        threading.Thread(target=self.run_code_in_thread, daemon=True).start()

    def run_code_in_thread(self):
        try:
            process = subprocess.Popen(
                ["python", "temp_code.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # 用于存储输出和错误信息
            output = []
            error = []

            # 用于处理 input 调用
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                if ">>> " in line:  # 检测到 input 提示符
                    user_input = self.get_user_input(line.strip(">>> "))
                    process.stdin.write(user_input + "\n")
                    process.stdin.flush()
                else:
                    output.append(line)

            # 获取剩余的输出和错误信息
            remaining_output = process.stdout.read()
            if remaining_output:
                output.append(remaining_output)
            remaining_error = process.stderr.read()
            if remaining_error:
                error.append(remaining_error)

            # 将输出和错误信息显示在输出区
            self.update_output_area(output, error)

        except Exception as e:
            self.update_output_area([], [str(e)])

    def get_user_input(self, prompt):
        self.output_area.config(state="normal")
        self.output_area.insert(tk.END, prompt + "\n")
        self.output_area.config(state="disabled")
        self.root.update_idletasks()
        user_input = tk.simpledialog.askstring("Input", prompt, parent=self.root)
        return user_input if user_input else ""

    def update_output_area(self, output, error):
        self.output_area.config(state="normal")
        self.output_area.delete(1.0, tk.END)
        if error:
            self.output_area.insert(tk.END, "".join(error), "error")
            self.output_area.tag_config("error", foreground="red")
        else:
            self.output_area.insert(tk.END, "".join(output))
        self.output_area.config(state="disabled")

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