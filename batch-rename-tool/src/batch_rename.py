"""
Batch Rename Tool — 批量重命名工具

A desktop GUI application for batch renaming files by creation time,
modification time, or filename, with customizable naming patterns.

Author: zj126-creator
License: MIT
Python: 3.8+
"""

import os
import sys
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    print("tkinter is required. Please ensure Python was installed with Tk/Tcl support.")
    sys.exit(1)


class BatchRenameApp:
    """Main application class for the batch rename tool."""

    def __init__(self, root):
        self.root = root
        self.root.title("批量重命名工具")
        self.root.geometry("820x620")
        self.root.minsize(700, 520)

        # ── State variables ──
        self.folder_path = tk.StringVar(value="")
        self.name_prefix = tk.StringVar(value="")
        self.name_suffix = tk.StringVar(value="")
        self.start_number = tk.StringVar(value="1")
        self.zero_pad = tk.StringVar(value="0")
        self.separator = tk.StringVar(value="_")
        self.sort_mode = tk.StringVar(value="created")
        self.reverse_sort = tk.BooleanVar(value=False)
        self.keep_extension = tk.BooleanVar(value=True)

        # Internal data
        self.preview_data = []  # [(old_path, sort_label), ...]
        self.history = []       # [(new_path, old_name), ...] for undo

        self._build_ui()

    # ──────────────────────────────────────────────
    #  UI Construction
    # ──────────────────────────────────────────────

    def _build_ui(self):
        """Build the complete UI layout."""
        self._build_folder_section()
        self._build_rules_section()
        self._build_preview_section()
        self._build_action_bar()

    def _build_folder_section(self):
        """Step 1: Folder selection."""
        top = ttk.LabelFrame(self.root, text="第一步：选择文件夹")
        top.pack(fill="x", padx=10, pady=(10, 5))

        row = ttk.Frame(top)
        row.pack(fill="x", padx=8, pady=8)
        ttk.Label(row, text="文件夹：").pack(side="left")
        ttk.Entry(row, textvariable=self.folder_path, width=55).pack(
            side="left", expand=True, fill="x", padx=5
        )
        ttk.Button(row, text="浏览…", command=self._browse_folder).pack(side="left")
        ttk.Button(row, text="扫描文件", command=self._scan_files).pack(
            side="left", padx=(5, 0)
        )

    def _build_rules_section(self):
        """Step 2: Naming rules configuration."""
        mid = ttk.LabelFrame(self.root, text="第二步：命名规则")
        mid.pack(fill="x", padx=10, pady=5)

        grid = ttk.Frame(mid)
        grid.pack(fill="x", padx=8, pady=8)

        # Prefix
        ttk.Label(grid, text="前缀：").grid(row=0, column=0, sticky="e", pady=4)
        ttk.Entry(grid, textvariable=self.name_prefix, width=18).grid(
            row=0, column=1, sticky="w", pady=4, padx=4
        )
        ttk.Label(grid, text="（可选，如：照片、IMG）").grid(row=0, column=2, sticky="w", pady=4)

        # Suffix
        ttk.Label(grid, text="后缀：").grid(row=1, column=0, sticky="e", pady=4)
        ttk.Entry(grid, textvariable=self.name_suffix, width=18).grid(
            row=1, column=1, sticky="w", pady=4, padx=4
        )
        ttk.Label(grid, text="（可选）").grid(row=1, column=2, sticky="w", pady=4)

        # Start number & separator
        ttk.Label(grid, text="起始编号：").grid(row=2, column=0, sticky="e", pady=4)
        ttk.Entry(grid, textvariable=self.start_number, width=10).grid(
            row=2, column=1, sticky="w", pady=4, padx=4
        )
        ttk.Label(grid, text="分隔符：").grid(row=2, column=2, sticky="e", pady=4)
        ttk.Entry(grid, textvariable=self.separator, width=6).grid(
            row=2, column=3, sticky="w", pady=4, padx=4
        )

        # Zero padding
        ttk.Label(grid, text="补零位数：").grid(row=3, column=0, sticky="e", pady=4)
        ttk.Entry(grid, textvariable=self.zero_pad, width=6).grid(
            row=3, column=1, sticky="w", pady=4, padx=4
        )
        ttk.Label(grid, text="（0=不补零，3=001,002…）").grid(row=3, column=2, sticky="w", pady=4)

        # Sort mode
        ttk.Label(grid, text="排序方式：").grid(row=4, column=0, sticky="e", pady=4)
        sort_frame = ttk.Frame(grid)
        sort_frame.grid(row=4, column=1, columnspan=3, sticky="w", pady=4, padx=4)
        ttk.Radiobutton(sort_frame, text="创建时间", variable=self.sort_mode, value="created").pack(side="left")
        ttk.Radiobutton(sort_frame, text="修改时间", variable=self.sort_mode, value="modified").pack(side="left", padx=8)
        ttk.Radiobutton(sort_frame, text="文件名", variable=self.sort_mode, value="name").pack(side="left")

        # Checkboxes
        ttk.Checkbutton(grid, text="倒序排列", variable=self.reverse_sort).grid(
            row=5, column=1, sticky="w", pady=2
        )
        ttk.Checkbutton(grid, text="保留原扩展名", variable=self.keep_extension).grid(
            row=5, column=2, sticky="w", pady=2
        )

    def _build_preview_section(self):
        """Step 3: Preview table."""
        preview_frame = ttk.LabelFrame(self.root, text="第三步：预览（扫描后显示）")
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("old_name", "sort_key", "new_name")
        self.tree = ttk.Treeview(
            preview_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.tree.heading("old_name", text="原文件名")
        self.tree.heading("sort_key", text="排序依据")
        self.tree.heading("new_name", text="新文件名")
        self.tree.column("old_name", width=280)
        self.tree.column("sort_key", width=180)
        self.tree.column("new_name", width=280)

        tree_scroll = ttk.Scrollbar(
            preview_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        tree_scroll.pack(side="right", fill="y", pady=8, padx=(0, 4))

    def _build_action_bar(self):
        """Bottom action bar with buttons and status."""
        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=(5, 10))

        self.btn_preview = ttk.Button(bottom, text="🔄 生成预览", command=self._generate_preview)
        self.btn_preview.pack(side="left")

        self.btn_execute = ttk.Button(
            bottom, text="✅ 执行重命名", command=self._execute_rename, state="disabled"
        )
        self.btn_execute.pack(side="left", padx=5)

        self.btn_undo = ttk.Button(
            bottom, text="↩ 撤销上次操作", command=self._undo, state="disabled"
        )
        self.btn_undo.pack(side="left")

        self.status_var = tk.StringVar(value="请选择文件夹并扫描文件。")
        ttk.Label(bottom, textvariable=self.status_var).pack(side="right")

    # ──────────────────────────────────────────────
    #  Core Logic
    # ──────────────────────────────────────────────

    def _browse_folder(self):
        """Open folder dialog and auto-scan on selection."""
        folder = filedialog.askdirectory(title="选择包含待重命名文件的文件夹")
        if folder:
            self.folder_path.set(folder)
            self._scan_files()

    def _scan_files(self):
        """Scan the selected folder for files and sort them."""
        folder = self.folder_path.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("提示", "请先选择有效的文件夹。")
            return

        # Collect files (non-recursive)
        files = []
        for entry in os.listdir(folder):
            full = os.path.join(folder, entry)
            if os.path.isfile(full):
                files.append(full)

        if not files:
            self.preview_data.clear()
            self.tree.delete(*self.tree.get_children())
            self.status_var.set("文件夹中没有文件。")
            self.btn_execute.config(state="disabled")
            return

        # Sort files
        sort_mode = self.sort_mode.get()
        reverse = self.reverse_sort.get()
        files.sort(key=lambda p: self._get_sort_key(p, sort_mode), reverse=reverse)

        # Build preview data with display labels
        self.preview_data = []
        for path in files:
            label = self._get_sort_label(path, sort_mode)
            self.preview_data.append((path, label))

        self._generate_preview()

    def _get_sort_key(self, path, sort_mode):
        """Return the sort key for a file based on the selected mode."""
        if sort_mode == "created":
            try:
                return os.stat(path).st_ctime
            except OSError:
                return 0
        elif sort_mode == "modified":
            try:
                return os.path.getmtime(path)
            except OSError:
                return 0
        else:
            return os.path.basename(path).lower()

    def _get_sort_label(self, path, sort_mode):
        """Return a human-readable label for the sort key in the preview table."""
        if sort_mode == "created":
            try:
                ts = os.stat(path).st_ctime
                return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            except OSError:
                return "?"
        elif sort_mode == "modified":
            try:
                ts = os.path.getmtime(path)
                return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            except OSError:
                return "?"
        else:
            return "按名称"

    def _build_new_name(self, old_name, index):
        """
        Construct the new filename based on current settings.

        Args:
            old_name: Original filename.
            index: Zero-based index into the sorted file list.

        Returns:
            The new filename string.
        """
        try:
            start = int(self.start_number.get())
        except ValueError:
            start = 1

        try:
            pad = int(self.zero_pad.get())
        except ValueError:
            pad = 0

        num = start + index
        num_str = str(num).zfill(pad) if pad > 0 else str(num)

        sep = self.separator.get()
        prefix = self.name_prefix.get().strip()
        suffix = self.name_suffix.get().strip()

        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(num_str)
        if suffix:
            parts.append(suffix)

        new_base = sep.join(parts) if sep else "".join(parts)

        if self.keep_extension.get():
            ext = os.path.splitext(old_name)[1]
            return new_base + ext
        return new_base

    def _generate_preview(self):
        """Generate and display the rename preview table."""
        if not self.preview_data:
            messagebox.showinfo("提示", "请先扫描文件夹。")
            return

        # Validate inputs
        try:
            start = int(self.start_number.get())
            if start < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("提示", "起始编号必须为非负整数。")
            return

        try:
            pad = int(self.zero_pad.get())
            if pad < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("提示", "补零位数必须为非负整数。")
            return

        # Populate table
        self.tree.delete(*self.tree.get_children())

        for idx, (old_path, sort_label) in enumerate(self.preview_data):
            old_name = os.path.basename(old_path)
            new_name = self._build_new_name(old_name, idx)
            self.tree.insert("", "end", values=(old_name, sort_label, new_name))

        self.btn_execute.config(state="normal")
        self.status_var.set(
            f"共 {len(self.preview_data)} 个文件待重命名。确认无误后点击「执行重命名」。"
        )

    def _execute_rename(self):
        """Execute the rename operation with conflict avoidance."""
        if not self.preview_data:
            return

        folder = self.folder_path.get().strip()

        # Confirm before executing
        if not messagebox.askyesno(
            "确认",
            f"确定对 {len(self.preview_data)} 个文件执行重命名吗？\n\n建议先备份文件。",
        ):
            return

        undo_log = []
        errors = []

        for idx, (old_path, _) in enumerate(self.preview_data):
            old_name = os.path.basename(old_path)
            new_name = self._build_new_name(old_name, idx)
            new_path = os.path.join(folder, new_name)

            # Skip if name unchanged
            if old_path == new_path:
                continue

            # Avoid overwriting existing files
            if os.path.exists(new_path):
                new_name, new_path = self._resolve_conflict(
                    new_name, new_base=self._build_new_name(old_name, idx).rsplit(".", 1)[0]
                    if self.keep_extension.get() else self._build_new_name(old_name, idx),
                    ext=os.path.splitext(old_name)[1] if self.keep_extension.get() else "",
                    folder=folder,
                )

            try:
                os.rename(old_path, new_path)
                undo_log.append((new_path, old_name))
            except OSError as e:
                errors.append(f"{old_name} → {new_name}: {e}")

        self.history = undo_log
        self.btn_undo.config(state="normal" if undo_log else "disabled")

        if errors:
            messagebox.showwarning(
                "部分失败",
                f"完成 {len(undo_log)} 个，失败 {len(errors)} 个：\n\n" + "\n".join(errors[:10]),
            )
        else:
            messagebox.showinfo("完成", f"成功重命名 {len(undo_log)} 个文件！")

        self.status_var.set(f"完成：成功 {len(undo_log)} 个，失败 {len(errors)} 个。")
        self._scan_files()

    def _resolve_conflict(self, new_name, new_base, ext, folder):
        """
        Find a non-conflicting filename by appending a counter.

        Returns:
            Tuple of (resolved_name, resolved_path).
        """
        counter = 1
        while True:
            if ext:
                candidate = f"{new_base}_{counter}{ext}"
            else:
                candidate = f"{new_base}_{counter}"
            test_path = os.path.join(folder, candidate)
            if not os.path.exists(test_path):
                return candidate, test_path
            counter += 1

    def _undo(self):
        """Undo the last rename operation."""
        if not self.history:
            return

        if not messagebox.askyesno(
            "确认", f"撤销上次 {len(self.history)} 个文件的重命名操作？"
        ):
            return

        errors = []
        count = 0
        for new_path, old_name in self.history:
            folder = os.path.dirname(new_path)
            old_path = os.path.join(folder, old_name)
            try:
                os.rename(new_path, old_path)
                count += 1
            except OSError as e:
                errors.append(f"{os.path.basename(new_path)} → {old_name}: {e}")

        self.history.clear()
        self.btn_undo.config(state="disabled")

        if errors:
            messagebox.showwarning(
                "部分失败",
                f"撤销 {count} 个，失败 {len(errors)} 个：\n\n" + "\n".join(errors[:10]),
            )
        else:
            messagebox.showinfo("完成", f"成功撤销 {count} 个文件的重命名。")

        self.status_var.set(f"撤销完成：恢复 {count} 个，失败 {len(errors)} 个。")
        self._scan_files()


def main():
    """Entry point: create root window and start the application."""
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("vista")
    except tk.TclError:
        pass

    BatchRenameApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
