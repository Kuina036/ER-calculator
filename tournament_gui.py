import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import glob
import os

# Custom Rounded Button (Design retained as requested previously)
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=120, height=40, radius=20, bg_color="#3498db", fg_color="white", hover_color="#2980b9"):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.fg_color = fg_color
        self.text_str = text
        self.radius = radius
        self.width = width
        self.height = height
        
        self.rect_id = self._draw_rounded_rect(2, 2, width-2, height-2, radius, bg_color)
        self.text_id = self.create_text(width/2, height/2, text=text, fill=fg_color, font=("Malgun Gothic", 10, "bold"))
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, color):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, smooth=True, fill=color, outline=color)

    def _on_click(self, event):
        if self.command: self.command()

    def _on_enter(self, event):
        self.itemconfig(self.rect_id, fill=self.hover_color, outline=self.hover_color)

    def _on_leave(self, event):
        self.itemconfig(self.rect_id, fill=self.bg_color, outline=self.bg_color)

class TournamentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ER Tournament Calculator")
        self.root.geometry("1000x750")
        
        # Color Theme
        self.colors = {
            "bg_main": "#F0F4F8", "bg_header": "#FFFFFF", "text_main": "#2C3E50", 
            "checkpoint": "#FFF9C4", 
            "btn_blue": "#5D9CEC", "btn_blue_h": "#4A89DC", 
            "btn_green": "#48CFAD", "btn_green_h": "#37BC9B",
            "btn_orange": "#FFCE54", "btn_orange_h": "#F6BB42", 
            "btn_red": "#ED5565", "btn_red_h": "#DA4453",
            "btn_grey": "#AAB2BD", "btn_grey_h": "#656D78", 
            "btn_dark": "#434A54", "btn_dark_h": "#323133"
        }

        self.root.configure(bg=self.colors["bg_main"])
        self.teams_data = {}  
        self.penalties = {}   
        self.valid_teams = set()
        self.loaded_files = [] 
        self.history = []      
        self.checkpoint_mode = False
        self.checkpoint_score = 50.0

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Revert to standard Treeview for stability and visibility
        style.configure("Treeview", 
                        background="white", 
                        foreground="#2C3E50", 
                        fieldbackground="white", 
                        rowheight=35, 
                        font=("Malgun Gothic", 10))
        
        style.configure("Treeview.Heading", 
                        background="white", 
                        foreground="#2C3E50", 
                        font=("Malgun Gothic", 11, "bold"), 
                        relief="flat")
        
        style.map("Treeview", 
                  background=[("selected", "#BBDEFB")], 
                  foreground=[("selected", "black")])

    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors["bg_header"], pady=20, padx=30)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_frame, text="ER Tournament Ranking", font=("Malgun Gothic", 20, "bold"), bg=self.colors["bg_header"], fg=self.colors["text_main"]).pack(side=tk.LEFT)

        btn_box = tk.Frame(header_frame, bg=self.colors["bg_header"])
        btn_box.pack(side=tk.RIGHT)

        def add_btn(parent, text, cmd, bg, hover, width=100):
            btn = RoundedButton(parent, text, cmd, bg_color=bg, hover_color=hover, fg_color="white", width=width, height=35, radius=18)
            btn.pack(side=tk.LEFT, padx=5)

        add_btn(btn_box, "설정", self.open_settings, self.colors["btn_dark"], self.colors["btn_dark_h"], 80)
        add_btn(btn_box, "파일 추가", self.upload_file, self.colors["btn_green"], self.colors["btn_green_h"])
        add_btn(btn_box, "파일 취소", self.undo_last_file, self.colors["btn_orange"], self.colors["btn_orange_h"])

        # Status
        self.lbl_status = tk.Label(self.root, text="준비 완료", bg=self.colors["bg_main"], fg="#656D78", font=("Malgun Gothic", 9))
        self.lbl_status.pack(fill=tk.X, padx=30, pady=(0, 5))

        # Main Table (Standard Treeview)
        table_frame = tk.Frame(self.root, bg="white", padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        cols = ("rank", "team", "total", "kill", "penalty")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        
        headers = {"rank": "순위", "team": "팀 이름", "total": "종합 점수", "kill": "킬 점수", "penalty": "패널티"}
        widths = {"rank": 60, "team": 300, "total": 120, "kill": 120, "penalty": 100}

        for col, text in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=widths[col], anchor="center" if col != "team" else "w")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("checkpoint", background=self.colors["checkpoint"])
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Footer
        footer_frame = tk.Frame(self.root, bg=self.colors["bg_main"], pady=20, padx=30)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_selected = tk.Label(footer_frame, text="선택된 팀: 없음", font=("Malgun Gothic", 12, "bold"), bg=self.colors["bg_main"], fg=self.colors["btn_blue"])
        self.lbl_selected.pack(side=tk.TOP, anchor="w", pady=(0, 15))

        btn_row = tk.Frame(footer_frame, bg=self.colors["bg_main"])
        btn_row.pack(side=tk.TOP, fill=tk.X)

        add_btn(btn_row, "금구사 (-1)", lambda: self.apply_penalty(1), "#FC6E51", "#E9573F", 110)
        add_btn(btn_row, "픽 (-3)", lambda: self.apply_penalty(3), self.colors["btn_red"], self.colors["btn_red_h"], 100)
        add_btn(btn_row, "실행 취소", self.undo_penalty, self.colors["btn_grey"], self.colors["btn_grey_h"])
        
        btn_reset = RoundedButton(btn_row, "초기화", lambda: self.apply_penalty(0, True), width=100, height=35, radius=18, bg_color="#656D78", hover_color="#434A54", fg_color="white")
        btn_reset.pack(side=tk.RIGHT)

    def normalize_name(self, name):
        return ' '.join(name.split())

    def upload_file(self):
        f = filedialog.askopenfilename(title="파일 선택", filetypes=[("CSV files", "*.csv")])
        if not f: return
        path = os.path.abspath(f)
        if path in self.loaded_files:
            messagebox.showinfo("알림", "이미 추가된 파일입니다.")
            return
        try:
            self.process_file(path, is_base=(len(self.valid_teams)==0))
            self.loaded_files.append(path)
            self.refresh_table()
            self.lbl_status.config(text=f"추가됨: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("오류", str(e))

    def undo_last_file(self):
        if self.loaded_files:
            removed = self.loaded_files.pop()
            self.recalculate_all()
            self.refresh_table()
            self.lbl_status.config(text=f"취소됨: {os.path.basename(removed)}")
        else:
            messagebox.showinfo("알림", "취소할 파일이 없습니다.")

    def recalculate_all(self):
        self.teams_data = {}
        self.valid_teams = set()
        for i, f in enumerate(self.loaded_files):
            self.process_file(f, is_base=(i==0))

    def process_file(self, path, is_base=False):
        for enc in ['utf-8-sig', 'cp949']:
            try:
                with open(path, 'r', encoding=enc) as csvfile:
                    reader = csv.DictReader(csvfile)
                    if reader.fieldnames:
                        reader.fieldnames = [n.strip() for n in reader.fieldnames]
                    if 'teamName' not in reader.fieldnames: continue
                    rows = list(reader)
                    if not rows: continue
                    
                    file_scores = {}
                    has_teams = False

                    for row in rows:
                        name = self.normalize_name(row.get('teamName', ''))
                        if not name: continue
                        has_teams = True
                        
                        if is_base: 
                            self.valid_teams.add(name)
                        elif name not in self.valid_teams:
                            raise ValueError(f"등록되지 않은 팀 발견: {name}\n\n이 팀은 첫 번째 파일(1라운드)에 존재하지 않습니다.")

                        try:
                            t = float(row.get('tournament total score', '0').strip() or 0)
                            k = float(row.get('tournament kill score', '0').strip() or 0)
                            file_scores[name] = (t, k)
                        except:
                            continue

                    if not has_teams: continue

                    for name, (t, k) in file_scores.items():
                        if name not in self.teams_data: 
                            self.teams_data[name] = {'total':0.0, 'kill':0.0}
                        self.teams_data[name]['total'] += t
                        self.teams_data[name]['kill'] += k
                    return 
            except ValueError as ve:
                raise ve
            except:
                continue
        
        raise ValueError("파일을 읽을 수 없거나 'teamName' 열을 찾을 수 없습니다.\n(CSV 인코딩 또는 헤더를 확인해주세요)")

    def refresh_table(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        ranks = []
        for team, d in self.teams_data.items():
            p = self.penalties.get(team, 0.0)
            final_total = d['total'] - p
            ranks.append({'team':team, 'total':final_total, 'kill':d['kill'], 'penalty':p})
        ranks.sort(key=lambda x: (x['total'], x['kill']), reverse=True)
        
        for i, item in enumerate(ranks):
            tag = ()
            if self.checkpoint_mode and item['total'] >= self.checkpoint_score:
                tag = ("checkpoint",)
            
            self.tree.insert("", "end", values=(
                i+1, 
                item['team'], 
                f"{item['total']:.1f}", 
                f"{item['kill']:.1f}", 
                f"-{item['penalty']:.1f}" if item['penalty']>0 else "0"
            ), tags=tag)

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if sel: 
            name = self.tree.item(sel[0])['values'][1]
            self.lbl_selected.config(text=f"선택된 팀: {name}")

    def apply_penalty(self, amt, reset=False):
        sel = self.tree.selection()
        if not sel: 
            messagebox.showwarning("주의", "팀을 먼저 선택해주세요.")
            return
            
        name = self.tree.item(sel[0])['values'][1]
        if reset: 
            self.penalties[name] = 0.0
            self.history = [h for h in self.history if h['team'] != name]
        else:
            self.penalties[name] = self.penalties.get(name, 0.0) + amt
            self.history.append({'team':name, 'amount':amt})
        self.refresh_table()

    def undo_penalty(self):
        if self.history:
            last = self.history.pop()
            self.penalties[last['team']] -= last['amount']
            self.refresh_table()
        else:
            messagebox.showinfo("알림", "취소할 작업이 없습니다.")

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("설정")
        win.geometry("320x240")
        win.configure(bg=self.colors["bg_main"])
        win.transient(self.root)  # Set as transient window
        win.grab_set()           # Make it modal
        
        # Exact centering logic
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()
        
        x = main_x + (main_w // 2) - 160
        y = main_y + (main_h // 2) - 120
        win.geometry(f"+{x}+{y}")
        
        # Header
        tk.Label(win, text="체크포인트 설정", font=("Malgun Gothic", 14, "bold"), 
                 bg=self.colors["bg_main"], fg=self.colors["text_main"]).pack(pady=(25, 10))
        
        # Checkbox with better styling
        var = tk.BooleanVar(value=self.checkpoint_mode)
        chk = tk.Checkbutton(win, text="체크포인트 모드 활성화", variable=var, 
                       bg=self.colors["bg_main"], activebackground=self.colors["bg_main"], 
                       selectcolor="white", font=("Malgun Gothic", 10))
        chk.pack(pady=5)
        
        # Input Frame
        f = tk.Frame(win, bg=self.colors["bg_main"])
        f.pack(pady=15)
        
        tk.Label(f, text="기준 점수:", bg=self.colors["bg_main"], 
                 font=("Malgun Gothic", 10, "bold"), fg=self.colors["text_main"]).pack(side=tk.LEFT)
                 
        ent = tk.Entry(f, width=10, font=("Malgun Gothic", 10), justify="center", relief="solid", bd=1)
        ent.insert(0, str(self.checkpoint_score))
        ent.pack(side=tk.LEFT, padx=10)
        
        def save():
            self.checkpoint_mode = var.get()
            try: self.checkpoint_score = float(ent.get())
            except: pass
            self.refresh_table()
            win.destroy()
        
        # Use RoundedButton instead of standard Button
        btn_save = RoundedButton(win, "저장하기", save, width=120, height=40, radius=20, 
                                 bg_color=self.colors["btn_blue"], hover_color=self.colors["btn_blue_h"])
        btn_save.pack(pady=(0, 20))

if __name__ == "__main__":
    root = tk.Tk()
    app = TournamentApp(root)
    root.mainloop()
