"""FSRS 间隔重复学习系统 - GUI 主程序"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.font import Font
from pathlib import Path
from datetime import datetime, timezone
import math, sys, os

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fsrs_trainer.fsrs import Scheduler, Card, Rating, State
from fsrs_trainer.question import Question, load_questions
from fsrs_trainer.storage import save_all_decks, load_all_decks

BG = "#f5f5f5"
CARD_BG = "#ffffff"
ACCENT = "#4a90d9"
ACCENT_H = "#357abd"
OK_CLR = "#27ae60"
NG_CLR = "#e74c3c"
FF = "Microsoft YaHei"


class FSRSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FSRS 间隔重复学习系统")
        self.root.geometry("800x600")
        self.root.configure(bg=BG)
        self.root.minsize(700, 500)
        self.scheduler = Scheduler()
        self.progress_path = Path.home() / ".fsrs_trainer" / "progress.json"
        # 多题库模型
        self.decks = []          # [{deck_id, deck_name, deck_path, questions, cards, study_days, current_day, new_cards_per_day, new_card_indices, new_card_ptr}]
        self.active_deck_id = None
        # 学习状态
        self.current_question = None
        self.current_card = None
        self.current_user_answer = []
        self.session_stats = {"done": 0, "ok": 0, "ng": 0}
        self.option_vars = []
        # 撤销
        self._undo_snapshot = None
        self._syncing_days = False
        self._build_welcome()

    # ────────────── 工具 ──────────────

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def _active_deck(self):
        for d in self.decks:
            if d['deck_id'] == self.active_deck_id:
                return d
        return None

    def _deck_id_from_path(self, path):
        return str(Path(path).resolve())

    def _make_deck(self, path, questions):
        deck_id = self._deck_id_from_path(path)
        return {
            'deck_id': deck_id,
            'deck_name': Path(path).name,
            'deck_path': path,
            'questions': questions,
            'cards': {},
            'study_days': 7,
            'current_day': 0,
            'new_cards_per_day': math.ceil(len(questions) / 7),
            'new_card_indices': list(range(len(questions))),
            'new_card_ptr': 0,
        }

    # ────────────── 持久化 ──────────────

    def _save_all(self):
        save_all_decks(str(self.progress_path), self.decks, self.active_deck_id)

    def _load_all(self):
        data = load_all_decks(str(self.progress_path))
        if not data:
            return
        self.decks = []
        for d in data.get('decks', []):
            deck_path = d.get('deck_path', '')
            if not deck_path or not Path(deck_path).exists():
                continue
            try:
                questions = load_questions(deck_path)
            except Exception:
                continue
            deck = {
                'deck_id': d.get('deck_id', self._deck_id_from_path(deck_path)),
                'deck_name': d.get('deck_name', Path(deck_path).name),
                'deck_path': deck_path,
                'questions': questions,
                'cards': d.get('cards', {}),
                'study_days': d.get('study_days', 7),
                'current_day': d.get('current_day', 0),
                'new_cards_per_day': d.get('new_cards_per_day', 0),
                'new_card_indices': d.get('new_card_indices', []),
                'new_card_ptr': d.get('new_card_ptr', 0),
            }
            self.decks.append(deck)
        self.active_deck_id = data.get('active_deck')
        if self.active_deck_id and not self._active_deck():
            if self.decks:
                self.active_deck_id = self.decks[0]['deck_id']
            else:
                self.active_deck_id = None

    # ────────────── 首页 ──────────────

    def _build_welcome(self):
        self._clear()
        f = ttk.Frame(self.root, padding=40)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text="FSRS 间隔重复学习系统",
                  font=Font(family=FF, size=20, weight="bold")).pack(pady=(20, 5))
        ttk.Label(f, text="基于 FSRS-5.0 算法的科学复习工具",
                  font=Font(family=FF, size=11)).pack(pady=(0, 25))
        ttk.Button(f, text="导入题库（CSV/Excel）",
                   command=self._import_deck).pack(pady=10, ipadx=20, ipady=6)

        # 题库列表区域
        list_frame = ttk.LabelFrame(f, text="已加载题库", padding=10)
        list_frame.pack(fill="x", pady=10)

        cols = ("name", "total", "learned", "days", "status")
        self.deck_tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=6)
        self.deck_tree.heading("name", text="题库")
        self.deck_tree.heading("total", text="总题数")
        self.deck_tree.heading("learned", text="已学")
        self.deck_tree.heading("days", text="计划天数")
        self.deck_tree.heading("status", text="状态")
        self.deck_tree.column("name", width=250, anchor="w")
        self.deck_tree.column("total", width=60, anchor="center")
        self.deck_tree.column("learned", width=60, anchor="center")
        self.deck_tree.column("days", width=70, anchor="center")
        self.deck_tree.column("status", width=80, anchor="center")
        self.deck_tree.pack(fill="x", pady=5)

        self.deck_tree.bind("<<TreeviewSelect>>", self._on_deck_select)
        self.deck_tree.bind("<Double-1>", lambda e: self._start_study())

        # 操作按钮
        bf = ttk.Frame(f)
        bf.pack(pady=8)
        self.start_btn = ttk.Button(bf, text="开始学习", command=self._start_study, state="disabled")
        self.start_btn.pack(side="left", padx=6)
        self.view_btn = ttk.Button(bf, text="查看题库", command=self._view_deck, state="disabled")
        self.view_btn.pack(side="left", padx=6)
        self.remove_btn = ttk.Button(bf, text="移除题库", command=self._remove_deck, state="disabled")
        self.remove_btn.pack(side="left", padx=6)
        self.undo_btn = ttk.Button(bf, text="撤销导入", command=self._undo_import, state="disabled")
        self.undo_btn.pack(side="left", padx=6)

        # 学习天数 + 统计
        df = ttk.Frame(f)
        df.pack(pady=10)
        ttk.Label(df, text="学习天数：", font=Font(family=FF, size=11)).pack(side="left")
        self.days_var = tk.IntVar(value=7)
        self.days_spin = ttk.Spinbox(df, from_=1, to=365, width=5, textvariable=self.days_var)
        self.days_spin.pack(side="left", padx=5)
        self.days_var.trace("w", self._on_days_changed)

        self.stats_label = ttk.Label(f, text="", font=Font(family=FF, size=11))
        self.stats_label.pack(pady=8)

        self._load_all()
        self._refresh_deck_list()

    def _refresh_deck_list(self):
        self.deck_tree.delete(*self.deck_tree.get_children())
        for d in self.decks:
            total = len(d['questions'])
            learned = sum(1 for c in d['cards'].values() if c.reps > 0)
            days = d.get('study_days', 7)
            current = d.get('current_day', 0)
            if learned == 0:
                status = "未开始"
            elif current < days:
                status = f"第{current+1}天"
            else:
                status = "复习中"
            self.deck_tree.insert("", "end", iid=d['deck_id'],
                                  values=(d['deck_name'], total, learned, days, status))
        has_decks = len(self.decks) > 0
        has_selection = self.active_deck_id is not None
        self.start_btn.config(state="normal" if has_selection else "disabled")
        self.view_btn.config(state="normal" if has_selection else "disabled")
        self.remove_btn.config(state="normal" if has_selection else "disabled")
        self.undo_btn.config(state="normal" if self._undo_snapshot else "disabled")
        if has_selection:
            d = self._active_deck()
            if d:
                # 同步天数到 spinbox（不触发 trace 回写）
                self._syncing_days = True
                self.days_var.set(d.get('study_days', 7))
                self._syncing_days = False
                learned = sum(1 for c in d['cards'].values() if c.reps > 0)
                total = len(d['questions'])
                self.stats_label.config(text=f"当前题库：{d['deck_name']}（{total} 题，已学 {learned} 题）")
            else:
                self.stats_label.config(text="")
        else:
            self.stats_label.config(text="")

    def _on_deck_select(self, event):
        sel = self.deck_tree.selection()
        if sel:
            self.active_deck_id = sel[0]
        self._refresh_deck_list()

    def _on_days_changed(self, *args):
        """学习天数变化时实时写入当前题库"""
        if getattr(self, '_syncing_days', False):
            return
        d = self._active_deck()
        if d:
            try:
                days = self.days_var.get()
                if days < 1:
                    days = 1
                d['study_days'] = days
                d['new_cards_per_day'] = math.ceil(len(d['questions']) / days)
                self._save_all()
                self._refresh_deck_list()
            except (tk.TclError, ValueError):
                pass

    # ────────────── 导入 / 移除 / 撤销 ──────────────

    def _import_deck(self):
        fp = filedialog.askopenfilename(
            title="选择题库文件",
            filetypes=[("CSV 题库", "*.csv"), ("Excel 题库", "*.xlsx;*.xls"), ("JSON 题库", "*.json"), ("所有文件", "*.*")])
        if not fp:
            return
        try:
            new_questions = load_questions(fp)
            if not new_questions:
                messagebox.showerror("错误", "题库为空或格式无效！")
                return
            deck_id = self._deck_id_from_path(fp)
            existing = None
            for d in self.decks:
                if d['deck_id'] == deck_id:
                    existing = d
                    break
            # 保存撤销快照
            self._undo_snapshot = {
                'decks': [{**d, 'cards': {k: v for k, v in d['cards'].items()}} for d in self.decks],
                'active_deck_id': self.active_deck_id,
            }
            if existing:
                existing['questions'] = new_questions
                learned = sum(1 for c in existing['cards'].values() if c.reps > 0)
                total = len(new_questions)
                self.active_deck_id = deck_id
                self._refresh_deck_list()
                messagebox.showinfo("导入成功", f"检测到同一题库，已保留学习进度！\n{existing['deck_name']}（共 {total} 题，已学 {learned} 题）")
            else:
                deck = self._make_deck(fp, new_questions)
                deck['study_days'] = self.days_var.get()
                deck['new_cards_per_day'] = math.ceil(len(new_questions) / deck['study_days'])
                self.decks.append(deck)
                self.active_deck_id = deck_id
                total = len(new_questions)
                self._refresh_deck_list()
                messagebox.showinfo("导入成功", f"成功导入 {total} 道题目！\n题库：{deck['deck_name']}\n当前共 {len(self.decks)} 个题库")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败：\n{e}")

    def _remove_deck(self):
        d = self._active_deck()
        if not d:
            return
        if not messagebox.askyesno("确认", f"确定要移除题库「{d['deck_name']}」吗？\n该题库的学习进度将被删除。"):
            return
        self._undo_snapshot = {
            'decks': [{**dd, 'cards': {k: v for k, v in dd['cards'].items()}} for dd in self.decks],
            'active_deck_id': self.active_deck_id,
        }
        self.decks = [dd for dd in self.decks if dd['deck_id'] != d['deck_id']]
        if self.active_deck_id == d['deck_id']:
            self.active_deck_id = self.decks[0]['deck_id'] if self.decks else None
        self._save_all()
        self._refresh_deck_list()
        messagebox.showinfo("已移除", f"题库「{d['deck_name']}」已移除")

    def _undo_import(self):
        if not self._undo_snapshot:
            return
        self.decks = self._undo_snapshot['decks']
        self.active_deck_id = self._undo_snapshot['active_deck_id']
        self._undo_snapshot = None
        self._refresh_deck_list()
        messagebox.showinfo("已撤销", "已恢复到操作前的状态")

    # ────────────── 查看题库 ──────────────

    def _view_deck(self):
        d = self._active_deck()
        if not d:
            return
        questions = d['questions']
        cards = d['cards']
        if not questions:
            messagebox.showinfo("题库", "当前题库为空")
            return
        win = tk.Toplevel(self.root)
        win.title(f"题库列表 - {d['deck_name']}")
        win.geometry("750x500")
        win.configure(bg=BG)
        total = len(questions)
        learned = sum(1 for c in cards.values() if c.reps > 0)
        type_map = {"single": "单选", "multiple": "多选", "judge": "判断"}
        ttk.Label(win, text=f"共 {total} 题 | 已学 {learned} | 待学 {total - learned}",
                  font=Font(family=FF, size=11)).pack(pady=8)
        sf = ttk.Frame(win)
        sf.pack(fill="x", padx=15, pady=5)
        ttk.Label(sf, text="搜索：", font=Font(family=FF, size=10)).pack(side="left")
        search_var = tk.StringVar()
        ttk.Entry(sf, textvariable=search_var, width=30).pack(side="left", padx=5)
        lf = ttk.Frame(win)
        lf.pack(fill="both", expand=True, padx=15, pady=5)
        cols = ("no", "type", "question", "status")
        tree = ttk.Treeview(lf, columns=cols, show="headings", height=20)
        tree.heading("no", text="序号")
        tree.heading("type", text="题型")
        tree.heading("question", text="题干")
        tree.heading("status", text="状态")
        tree.column("no", width=50, anchor="center")
        tree.column("type", width=60, anchor="center")
        tree.column("question", width=500, anchor="w")
        tree.column("status", width=80, anchor="center")
        sb = ttk.Scrollbar(lf, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def refresh(keyword=""):
            tree.delete(*tree.get_children())
            for i, q in enumerate(questions):
                if keyword and keyword.lower() not in q.question.lower():
                    continue
                c = cards.get(q.id)
                status = f"已学({c.reps}次)" if c and c.reps > 0 else "待学"
                tree.insert("", "end", values=(i + 1, type_map.get(q.type, q.type),
                                               q.question[:60] + ("..." if len(q.question) > 60 else ""), status))
        refresh()
        search_var.trace("write", lambda *a: refresh(search_var.get().strip()))

        def on_dbl(event):
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], "values")
            idx = int(vals[0]) - 1
            if 0 <= idx < len(questions):
                q = questions[idx]
                dw = tk.Toplevel(win)
                dw.title(f"题目详情 - 第 {idx+1} 题")
                dw.geometry("600x400")
                dw.configure(bg=BG)
                ttk.Label(dw, text=f"题型：{type_map.get(q.type, q.type)}", font=Font(family=FF, size=11)).pack(anchor="w", padx=20, pady=(15, 5))
                ttk.Label(dw, text="题目：", font=Font(family=FF, size=11, weight="bold")).pack(anchor="w", padx=20, pady=(5, 2))
                ttk.Label(dw, text=q.question, font=Font(family=FF, size=11), wraplength=550, justify="left").pack(anchor="w", padx=20, pady=5)
                if q.options:
                    ttk.Label(dw, text="选项：", font=Font(family=FF, size=11, weight="bold")).pack(anchor="w", padx=20, pady=(10, 2))
                    for j, opt in enumerate(q.options):
                        mark = " ✓" if j in q.answer else ""
                        ttk.Label(dw, text=f"{chr(65+j)}. {opt}{mark}", font=Font(family=FF, size=10), wraplength=550, justify="left").pack(anchor="w", padx=25, pady=2)
                ttk.Label(dw, text=f"答案：{q.get_correct_text()}", font=Font(family=FF, size=11), foreground=OK_CLR).pack(anchor="w", padx=20, pady=(10, 5))
                if q.explanation:
                    ttk.Label(dw, text=f"解析：{q.explanation}", font=Font(family=FF, size=10), wraplength=550, justify="left").pack(anchor="w", padx=20, pady=5)
        tree.bind("<Double-1>", on_dbl)
        ttk.Button(win, text="关闭", command=win.destroy).pack(pady=10)

    # ────────────── 学习流程 ──────────────

    def _start_study(self):
        d = self._active_deck()
        if not d:
            return
        d['study_days'] = self.days_var.get()
        d['new_cards_per_day'] = math.ceil(len(d['questions']) / d['study_days'])
        d['new_card_indices'] = list(range(len(d['questions'])))
        d['new_card_ptr'] = 0
        d['current_day'] = 0
        self.session_stats = {"done": 0, "ok": 0, "ng": 0}
        self._build_study()
        self._next_q()

    def _build_study(self):
        d = self._active_deck()
        self._clear()
        f = ttk.Frame(self.root, padding=30)
        f.pack(fill="both", expand=True)
        top = ttk.Frame(f)
        top.pack(fill="x", pady=(0, 12))
        deck_name = d['deck_name'] if d else ""
        self.day_label = ttk.Label(top, text=f"[{deck_name}] 第 {d['current_day']+1} 天", font=Font(family=FF, size=10))
        self.day_label.pack(side="left")
        self.progress_label = ttk.Label(top, text="", font=Font(family=FF, size=10))
        self.progress_label.pack(side="right")
        self.stats_top = ttk.Label(top, text="", font=Font(family=FF, size=10))
        self.stats_top.pack(side="right", padx=20)
        card = tk.Frame(f, bg=CARD_BG, relief="solid", bd=1)
        card.pack(fill="both", expand=True, pady=8)
        self.type_label = tk.Label(card, text="", bg=CARD_BG, font=Font(family=FF, size=9), fg="#888888")
        self.type_label.pack(anchor="w", padx=20, pady=(12, 4))
        self.question_label = tk.Label(card, text="", bg=CARD_BG,
                                       font=Font(family=FF, size=14, weight="bold"),
                                       wraplength=650, justify="left", anchor="nw")
        self.question_label.pack(fill="x", padx=20, pady=(4, 12))
        self.options_frame = tk.Frame(card, bg=CARD_BG)
        self.options_frame.pack(fill="x", padx=20, pady=(0, 12))
        self.submit_btn = tk.Button(f, text="提交答案", font=Font(family=FF, size=11),
                                    bg=ACCENT, fg="white", activebackground=ACCENT_H,
                                    activeforeground="white", relief="flat",
                                    command=self._submit, cursor="hand2", padx=25, pady=6)
        self.submit_btn.pack(pady=8)
        ttk.Button(f, text="结束本次学习", command=self._end_study).pack(pady=4)

    def _build_feedback(self):
        self._clear()
        f = ttk.Frame(self.root, padding=30)
        f.pack(fill="both", expand=True)
        self.result_label = ttk.Label(f, text="", font=Font(family=FF, size=18, weight="bold"))
        self.result_label.pack(pady=(20, 10))
        self.ans_label = ttk.Label(f, text="", font=Font(family=FF, size=11), wraplength=650, justify="left")
        self.ans_label.pack(pady=10)
        self.explain_label = ttk.Label(f, text="", font=Font(family=FF, size=10), wraplength=650, justify="left")
        self.explain_label.pack(pady=10)
        ttk.Separator(f).pack(fill="x", pady=12)
        ttk.Label(f, text="请评价你的记忆情况（FSRS 将据此安排下次复习）：",
                  font=Font(family=FF, size=11)).pack(pady=(5, 12))
        rf = ttk.Frame(f)
        rf.pack(pady=10)
        for text, clr, rt in [("忘记了\nAgain", "#e74c3c", Rating.AGAIN),
                               ("很吃力\nHard", "#f39c12", Rating.HARD),
                               ("记住了\nGood", "#27ae60", Rating.GOOD),
                               ("很轻松\nEasy", "#2ecc71", Rating.EASY)]:
            tk.Button(rf, text=text, font=Font(family=FF, size=11), bg=clr, fg="white",
                      activebackground=clr, relief="flat", cursor="hand2",
                      command=lambda r=rt: self._rate(r), width=12, height=3).pack(side="left", padx=8)

    def _build_done(self):
        self._clear()
        f = ttk.Frame(self.root, padding=40)
        f.pack(fill="both", expand=True)
        d = self._active_deck()
        deck_name = d['deck_name'] if d else ""
        ttk.Label(f, text=f"[{deck_name}] 本次学习完成！",
                  font=Font(family=FF, size=20, weight="bold")).pack(pady=(30, 20))
        stats = self.session_stats
        rate = stats["ok"] / max(1, stats["done"]) * 100
        txt = f"完成题目：{stats['done']}\n答对：{stats['ok']}\n答错：{stats['ng']}\n正确率：{rate:.1f}%\n\n明天见！"
        ttk.Label(f, text=txt, font=Font(family=FF, size=12), justify="center").pack(pady=20)
        ttk.Button(f, text="返回首页", command=self._build_welcome).pack(pady=20, ipadx=15, ipady=6)

    def _get_due(self):
        d = self._active_deck()
        if not d:
            return []
        now = datetime.now(timezone.utc)
        due = []
        for q in d['questions']:
            c = d['cards'].get(q.id)
            if c and c.state != State.NEW and self.scheduler.is_due(c, now):
                due.append((q, c))
        if d['new_card_ptr'] < len(d['new_card_indices']):
            cnt = 0
            while d['new_card_ptr'] < len(d['new_card_indices']) and cnt < d['new_cards_per_day']:
                idx = d['new_card_indices'][d['new_card_ptr']]
                q = d['questions'][idx]
                c = d['cards'].get(q.id)
                if c is None:
                    c = Card()
                    d['cards'][q.id] = c
                if c.state == State.NEW:
                    due.append((q, c))
                    cnt += 1
                d['new_card_ptr'] += 1
        return due

    def _next_q(self):
        d = self._active_deck()
        if not d:
            self._build_welcome()
            return
        due = self._get_due()
        if not due:
            self._save_all()
            self._build_done()
            return
        self.current_question, self.current_card = due[0]
        self.current_user_answer = []
        self.progress_label.config(text=f"剩余：{len(due)}")
        self.stats_top.config(text=f"已做：{self.session_stats['done']} | 答对：{self.session_stats['ok']} | 答错：{self.session_stats['ng']}")
        self.day_label.config(text=f"[{d['deck_name']}] 第 {d['current_day']+1} 天 / 共 {d['study_days']} 天")
        tn = {"single": "单选题", "multiple": "多选题", "judge": "判断题"}
        self.type_label.config(text=tn.get(self.current_question.type, self.current_question.type))
        self.question_label.config(text=self.current_question.question)
        for w in self.options_frame.winfo_children():
            w.destroy()
        self.option_vars = []
        is_multi = self.current_question.type == "multiple"
        for i, opt in enumerate(self.current_question.options):
            v = tk.IntVar(value=0)
            self.option_vars.append(v)
            if is_multi:
                tk.Checkbutton(self.options_frame, text=opt, variable=v, bg=CARD_BG,
                               activebackground=CARD_BG, font=Font(family=FF, size=11),
                               anchor="w", cursor="hand2").pack(fill="x", pady=3, anchor="w")
            else:
                tk.Radiobutton(self.options_frame, text=opt, variable=v, value=i+1, bg=CARD_BG,
                               activebackground=CARD_BG, font=Font(family=FF, size=11),
                               anchor="w", cursor="hand2").pack(fill="x", pady=3, anchor="w")

    def _submit(self):
        if not self.current_question:
            return
        self.current_user_answer = [i for i, v in enumerate(self.option_vars) if v.get()]
        if not self.current_user_answer:
            messagebox.showwarning("提示", "请选择一个答案！")
            return
        ok = self.current_question.check_answer(self.current_user_answer)
        self.session_stats["done"] += 1
        if ok:
            self.session_stats["ok"] += 1
        else:
            self.session_stats["ng"] += 1
        self._build_feedback()
        self.result_label.config(text="回答正确！" if ok else "回答错误！", foreground=OK_CLR if ok else NG_CLR)
        ua = " / ".join(self.current_question.options[i] if i < len(self.current_question.options) else str(i) for i in sorted(self.current_user_answer))
        self.ans_label.config(text=f"正确答案：{self.current_question.get_correct_text()}\n你的答案：{ua}")
        self.explain_label.config(text=f"解析：{self.current_question.explanation}" if self.current_question.explanation else "")

    def _rate(self, rating):
        if self.current_card is None:
            return
        self.scheduler.schedule(self.current_card, rating)
        self._save_all()
        self._next_q()

    def _end_study(self):
        self._save_all()
        self._build_welcome()


def main():
    root = tk.Tk()
    FSRSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
