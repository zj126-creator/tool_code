#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面照片处理工具 —— 大小压缩 & 标准证件照制作
=============================================
功能：
  1. 照片文件大小压缩（迭代逼近目标值，支持 50 KB ~ 1 MB 自定义）
  2. 标准证件照制作（1寸/2寸，蓝底/白底，含自动去背景）

依赖安装（清华镜像）：
  pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "rembg[cpu]" Pillow

打包成 exe：
  pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyinstaller
  然后执行本文底部注释的打包命令。
"""

import os
import sys
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from threading import Thread

# ---------------------------------------------------------------------------
# 依赖检查：友好提示缺失库
# ---------------------------------------------------------------------------
# 【重要】在导入 rembg 前设置环境变量，禁用 pymatting（避免 numba 兼容性问题）
os.environ.setdefault("REMBG_USE_PYMATTING", "0")
os.environ.setdefault("REMBG_PROVIDER", "cpu")

# 打包成 exe 后，需要确保 sys._MEIPASS 在导入路径中
if getattr(sys, "frozen", False):
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and meipass not in sys.path:
        sys.path.insert(0, meipass)

# 先检查 Pillow
_MISSING_PKGS = []
try:
    from PIL import Image, ImageTk, ImageOps
except ImportError:
    _MISSING_PKGS.append("Pillow")

# 顶层导入 rembg（让 PyInstaller 能检测到依赖）
# 如果导入失败，会在具体功能函数中给出提示
try:
    import rembg
except Exception:
    pass

# 如果 Pillow 缺失，直接退出
if _MISSING_PKGS:
    msg = "缺少必要依赖库：Pillow\n\n请运行以下命令安装：\npip install -i https://pypi.tuna.tsinghua.edu.cn/simple Pillow"
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("依赖缺失", msg)
        root.destroy()
    except Exception:
        print(msg)
    sys.exit(1)

# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------
# 证件照规格（像素，300 DPI）
ID_PHOTO_SPECS = {
    "1寸蓝底": {
        "size_px": (295, 413),
        "dpi": 300,
        "bg_color": (67, 142, 219),  # 标准蓝底 RGB
    },
    "2寸蓝底": {
        "size_px": (413, 579),
        "dpi": 300,
        "bg_color": (67, 142, 219),
    },
    "1寸白底": {
        "size_px": (295, 413),
        "dpi": 300,
        "bg_color": (255, 255, 255),
    },
    "2寸白底": {
        "size_px": (413, 579),
        "dpi": 300,
        "bg_color": (255, 255, 255),
    },
}

# 压缩质量上下限
QUALITY_MIN = 5
QUALITY_MAX = 95


# ---------------------------------------------------------------------------
# 模型路径管理：支持打包后的 exe 和开发环境
# ---------------------------------------------------------------------------
MODEL_NAME = "u2net"         # 模型名称（u2net = 176 MB 高精度 / u2netp = 轻量版）
MODEL_FILENAME = "u2net.onnx"  # 对应的模型文件名


def get_model_path() -> str:
    """
    获取 u2net.onnx 模型文件的路径。
    优先查找打包后的 exe 同级目录，再查找开发环境的工作目录。
    """
    # 1) 如果是打包后的 exe，查找 exe 所在目录
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).parent
    else:
        # 2) 开发环境：脚本所在目录
        base_dir = Path(__file__).parent

    # 尝试多个可能的路径
    candidates = [
        base_dir / MODEL_FILENAME,
        base_dir / "models" / MODEL_FILENAME,
        Path.cwd() / MODEL_FILENAME,
    ]

    work_dir = Path.cwd()
    candidates.append(work_dir / MODEL_FILENAME)

    for p in candidates:
        if p.exists() and p.is_file():
            return str(p.resolve())

    return ""


def ensure_rembg_model(parent_window=None) -> bool:
    """
    确保 u2net 模型可用。
    优先使用本地模型文件，其次尝试自动下载（176 MB，首次使用需等待）。

    返回 True 表示模型可用，False 表示不可用。
    """
    model_path = get_model_path()

    if model_path:
        # 有本地模型文件，设置环境变量让 rembg 使用它
        os.environ["REMBG_MODEL_PATH"] = model_path
        return True

    # 没有本地模型，尝试自动下载
    if parent_window is not None:
        return download_model_with_progress(parent_window)

    return False


def download_model_with_progress(parent_window) -> bool:
    """
    下载 u2net 模型（176 MB），显示进度弹窗。
    在用户电脑上首次使用时调用。
    """
    import rembg.sessions.u2net as u2net_mod

    # 弹窗
    dlg = tk.Toplevel(parent_window)
    dlg.title("正在下载模型")
    dlg.geometry("420x160")
    dlg.resizable(False, False)
    dlg.transient(parent_window)
    dlg.grab_set()

    dlg.update_idletasks()
    x = parent_window.winfo_x() + (parent_window.winfo_width() - 420) // 2
    y = parent_window.winfo_y() + (parent_window.winfo_height() - 160) // 2
    dlg.geometry(f"+{x}+{y}")

    tk.Label(
        dlg,
        text="首次使用证件照功能需要下载 AI 模型\n"
             "（约 176 MB，下载较慢，请耐心等待）\n"
             "若下载失败，请手动下载 u2net.onnx 放到本程序同目录",
        wraplength=380,
        justify="center",
    ).pack(pady=(12, 8))

    progress_bar = ttk.Progressbar(dlg, mode="indeterminate", length=360)
    progress_bar.pack(pady=4)
    progress_bar.start(10)

    status_label = tk.Label(dlg, text="正在连接下载服务器...", fg="gray")
    status_label.pack()

    dlg.update()

    result = {"success": False}

    def download_task():
        try:
            u2net_mod.U2netSession.download_models()
            result["success"] = True
        except Exception as e:
            result["success"] = False
            result["msg"] = str(e)
        finally:
            parent_window.after(0, on_download_done)

    def on_download_done():
        dlg.destroy()
        if result["success"]:
            messagebox.showinfo(
                "模型下载完成",
                "AI 模型（u2net）已下载完成，现在可以正常使用证件照功能了！",
            )
        else:
            messagebox.showerror(
                "模型下载失败",
                f"{result.get('msg', '未知错误')}\n\n"
                "请确保网络稳定，或尝试手动下载：\n"
                "1. 下载 u2net.onnx（约 176 MB）\n"
                "2. 放到本程序同目录下\n"
                "3. 重新运行本程序",
            )

    Thread(target=download_task, daemon=True).start()
    parent_window.wait_window(dlg)
    return result["success"]


def create_u2net_session():
    """
    创建一个使用 u2net 模型的 rembg session。
    优先使用本地模型文件。
    u2net 模型（~168 MB）精度更高，去背景效果更好。
    """
    model_path = get_model_path()
    if model_path:
        os.environ["REMBG_MODEL_PATH"] = model_path

    # 补丁：绕过 pooch 的 checksum 校验，直接使用本地模型文件
    # 避免因 checksum 不匹配而重复下载 176 MB 的大模型
    import pooch.core as _pooch_core
    _original_retrieve = _pooch_core.retrieve

    def _patched_retrieve(url, known_hash=None, fname=None, path=None, **kwargs):
        if fname and path:
            full_path = os.path.join(str(path), fname) if isinstance(path, str) else os.path.join(str(path), fname)
            if os.path.exists(full_path) and os.path.getsize(full_path) > 1000000:
                return full_path
        return _original_retrieve(url, known_hash=None, fname=fname, path=path, **kwargs)

    _pooch_core.retrieve = _patched_retrieve

    return rembg.new_session("u2net")


# ---------------------------------------------------------------------------
# 核心功能一：照片文件大小压缩
# ---------------------------------------------------------------------------

def compress_image_to_target(
    input_path: str,
    output_path: str,
    target_size_bytes: int,
    max_iterations: int = 30,
    tolerance: float = 0.05,
) -> dict:
    """
    迭代压缩图片，使输出文件大小尽可能接近 target_size_bytes。

    策略：先降低 JPEG 质量，如果质量降到最低仍不够，再降低分辨率。

    参数：
        input_path        : 源图片路径
        output_path       : 输出图片路径
        target_size_bytes : 目标文件大小（字节）
        max_iterations    : 最大迭代次数
        tolerance         : 容忍误差比例（0.05 = ±5%）

    返回：
        dict: {"success": bool, "final_size": int, "iterations": int, "msg": str}
    """
    img = Image.open(input_path).convert("RGB")
    orig_width, orig_height = img.size
    orig_size = os.path.getsize(input_path)

    # 如果原图已经小于目标大小，直接保存
    if orig_size <= target_size_bytes:
        img.save(output_path, format="JPEG", quality=QUALITY_MAX)
        final_size = os.path.getsize(output_path)
        return {
            "success": True,
            "final_size": final_size,
            "iterations": 0,
            "msg": f"原图已小于目标大小，直接保存（{final_size / 1024:.1f} KB）",
        }

    # ---- 迭代压缩策略：先降质量，再降分辨率 ----
    quality = QUALITY_MAX
    scale = 1.0
    best_result = None

    for iteration in range(1, max_iterations + 1):
        # 如果需要缩放，先缩放图片
        if scale < 1.0:
            w = max(1, int(orig_width * scale))
            h = max(1, int(orig_height * scale))
            working_img = img.resize((w, h), Image.LANCZOS)
        else:
            working_img = img

        # 尝试保存到内存缓冲区，检查大小
        buf = io.BytesIO()
        working_img.save(buf, format="JPEG", quality=quality, optimize=True)
        current_size = buf.tell()

        # 记录最佳结果
        if best_result is None or abs(current_size - target_size_bytes) < abs(
            best_result["size"] - target_size_bytes
        ):
            best_result = {
                "size": current_size,
                "quality": quality,
                "scale": scale,
                "img": working_img.copy() if scale < 1.0 else img,
            }

        # 检查是否在容忍范围内
        if abs(current_size - target_size_bytes) / max(target_size_bytes, 1) <= tolerance:
            with open(output_path, "wb") as f:
                f.write(buf.getvalue())
            return {
                "success": True,
                "final_size": current_size,
                "iterations": iteration,
                "msg": (
                    f"压缩成功！{current_size / 1024:.1f} KB / "
                    f"目标 {target_size_bytes / 1024:.1f} KB "
                    f"（质量={quality}, 缩放={scale:.2f}）"
                ),
            }

        # 调整参数：太大则降质量/分辨率，太小则升质量
        if current_size > target_size_bytes:
            if quality > 20:
                quality = max(QUALITY_MIN, quality - 5)
            else:
                scale *= 0.85
                quality = max(QUALITY_MIN, quality - 2)
        else:
            if quality < QUALITY_MAX:
                quality = min(QUALITY_MAX, quality + 5)
            else:
                if scale < 1.0:
                    scale = min(1.0, scale + 0.05)
                else:
                    break

    # 使用最佳结果保存
    if best_result:
        best_img = best_result["img"]
        best_quality = best_result["quality"]
        best_img.save(output_path, format="JPEG", quality=best_quality, optimize=True)
        final_size = os.path.getsize(output_path)
        return {
            "success": True,
            "final_size": final_size,
            "iterations": max_iterations,
            "msg": (
                f"迭代完成，最终 {final_size / 1024:.1f} KB / "
                f"目标 {target_size_bytes / 1024:.1f} KB "
                f"（质量={best_quality}, 缩放={best_result['scale']:.2f}）"
            ),
        }

    return {
        "success": False,
        "final_size": 0,
        "iterations": max_iterations,
        "msg": "压缩失败，无法处理该图片",
    }


# ---------------------------------------------------------------------------
# 核心功能二：标准证件照制作
# ---------------------------------------------------------------------------

def make_id_photo(
    input_path: str,
    output_path: str,
    spec_name: str,
) -> dict:
    """
    生成标准证件照。

    使用 rembg + u2net 模型自动去除背景，
    缩放到目标尺寸，合成到对应颜色的纯色背景上。

    参数：
        input_path  : 源图片路径
        output_path : 输出图片路径
        spec_name   : 规格名称（如 "1寸蓝底"）

    返回：
        dict: {"success": bool, "msg": str, "has_warning": bool}
    """
    if spec_name not in ID_PHOTO_SPECS:
        return {"success": False, "msg": f"未知规格：{spec_name}", "has_warning": False}

    spec = ID_PHOTO_SPECS[spec_name]
    target_w, target_h = spec["size_px"]
    bg_color = spec["bg_color"]

    try:
        img = Image.open(input_path).convert("RGB")

        # ---- 去除背景 ----
        try:
            session = create_u2net_session()
            img_no_bg = rembg.remove(img, session=session)
        except Exception as e:
            return {
                "success": False,
                "msg": f"自动去背景失败（{e}）。\n请检查模型文件是否可用，或使用已手动处理背景的照片。",
                "has_warning": False,
            }

        # ---- 检查去背景效果 ----
        alpha = img_no_bg.split()[-1]
        alpha_arr = list(alpha.getdata())
        total_pixels = len(alpha_arr)
        fully_opaque = sum(1 for p in alpha_arr if p > 240)
        fully_transparent = sum(1 for p in alpha_arr if p < 15)
        opaque_ratio = fully_opaque / total_pixels if total_pixels > 0 else 0
        transparent_ratio = fully_transparent / total_pixels if total_pixels > 0 else 0

        has_warning = False
        warning_msg = ""
        if opaque_ratio > 0.95:
            has_warning = True
            warning_msg = "⚠️ 去背景效果可能不佳（背景未被有效去除），建议使用已手动处理的照片。"
        elif transparent_ratio > 0.95:
            has_warning = True
            warning_msg = "⚠️ 去背景后前景几乎完全透明，请使用包含人像的照片重试。"

        # ---- 缩放到证件照尺寸（保持比例，居中裁剪） ----
        fg = img_no_bg
        fg_w, fg_h = fg.size
        # 计算缩放比例：使图片完全覆盖目标尺寸
        scale_ratio = max(target_w / fg_w, target_h / fg_h)
        new_w = max(target_w, int(fg_w * scale_ratio))
        new_h = max(target_h, int(fg_h * scale_ratio))
        fg = fg.resize((new_w, new_h), Image.LANCZOS)

        # 居中裁剪
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        fg = fg.crop((left, top, left + target_w, top + target_h))

        # ---- 合成到纯色背景 ----
        bg = Image.new("RGBA", (target_w, target_h), bg_color + (255,))
        bg.paste(fg, (0, 0), fg)

        # ---- 保存为 JPEG ----
        result = bg.convert("RGB")
        result.save(output_path, format="JPEG", quality=95, dpi=(300, 300))

        msg = f"✅ 已生成 {spec_name} 证件照\n路径：{output_path}"
        if has_warning:
            msg += f"\n{warning_msg}"

        return {"success": True, "msg": msg, "has_warning": has_warning}

    except Exception as e:
        return {"success": False, "msg": f"处理失败：{e}", "has_warning": False}


# ---------------------------------------------------------------------------
# GUI 界面
# ---------------------------------------------------------------------------

class PhotoToolApp:
    """主应用窗口"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("照片处理工具 v1.0")
        self.root.resizable(False, False)
        self.root.geometry("640x540")

        # 变量
        self.input_path = tk.StringVar()
        self.target_size_kb = tk.StringVar(value="200")
        self.status_text = tk.StringVar(value="就绪，请选择图片")
        self._model_checked = False  # 是否已检查过模型

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ============================================================
        # 文件选择区域
        # ============================================================
        file_frame = ttk.LabelFrame(main_frame, text=" 选择照片 ", padding=8)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        row1 = ttk.Frame(file_frame)
        row1.pack(fill=tk.X)
        ttk.Button(row1, text="📂 浏览图片", command=self._on_select_file).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Entry(row1, textvariable=self.input_path, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        self.preview_label = ttk.Label(file_frame, text="（未选择图片）")
        self.preview_label.pack(pady=(6, 0))

        # ============================================================
        # 功能一：文件大小压缩
        # ============================================================
        comp_frame = ttk.LabelFrame(main_frame, text=" 功能一：文件大小压缩 ", padding=8)
        comp_frame.pack(fill=tk.X, pady=(0, 10))

        row2a = ttk.Frame(comp_frame)
        row2a.pack(fill=tk.X)
        ttk.Label(row2a, text="目标大小（KB）：").pack(side=tk.LEFT)
        ttk.Entry(row2a, textvariable=self.target_size_kb, width=12).pack(
            side=tk.LEFT, padx=(4, 0)
        )
        ttk.Label(row2a, text="（范围 50 ~ 1024 KB）").pack(side=tk.LEFT, padx=(6, 0))

        row2b = ttk.Frame(comp_frame)
        row2b.pack(fill=tk.X, pady=(6, 0))
        self.btn_compress = ttk.Button(
            row2b, text="⬇ 开始压缩", command=self._on_compress
        )
        self.btn_compress.pack(side=tk.LEFT)

        # ============================================================
        # 功能二：标准证件照制作
        # ============================================================
        id_frame = ttk.LabelFrame(main_frame, text=" 功能二：标准证件照制作 ", padding=8)
        id_frame.pack(fill=tk.X, pady=(0, 10))

        # 说明文字
        ttk.Label(
            id_frame,
            text="选择规格后自动去背景并合成证件照（首次使用需下载 AI 模型）",
            wraplength=580,
            foreground="gray",
        ).pack(anchor=tk.W, pady=(0, 6))

        row3 = ttk.Frame(id_frame)
        row3.pack(fill=tk.X)
        self.id_btns = {}
        for spec in ID_PHOTO_SPECS:
            btn = ttk.Button(
                row3,
                text=spec,
                width=14,
                command=lambda s=spec: self._on_make_id(s),
            )
            btn.pack(side=tk.LEFT, padx=3, pady=3)
            self.id_btns[spec] = btn

        # ============================================================
        # 状态栏
        # ============================================================
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.progress = ttk.Progressbar(
            status_frame, mode="indeterminate", length=300
        )
        self.status_label = ttk.Label(
            status_frame, textvariable=self.status_text, anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------

    def _on_select_file(self):
        """选择图片文件"""
        path = filedialog.askopenfilename(
            title="选择照片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        self.input_path.set(path)
        # 显示缩略图预览
        try:
            img = Image.open(path)
            img.thumbnail((120, 120))
            self._tk_img = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self._tk_img, text="")
        except Exception:
            self.preview_label.config(image="", text="（预览加载失败）")
        self.status_text.set(f"已选择：{Path(path).name}")

    def _on_compress(self):
        """压缩按钮点击处理"""
        src = self.input_path.get()
        if not src or not os.path.isfile(src):
            messagebox.showwarning("提示", "请先选择一张照片。")
            return

        # 校验目标大小
        try:
            target_kb = float(self.target_size_kb.get().strip())
            if target_kb < 50 or target_kb > 1024:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "提示", "目标大小请输入 50 ~ 1024 之间的数值（KB）。"
            )
            return

        target_bytes = int(target_kb * 1024)
        src_path = Path(src)
        out_path = src_path.parent / f"{src_path.stem}_压缩{src_path.suffix}"

        self._set_busy(True)
        self.status_text.set("⏳ 正在压缩，请稍候...")

        def task():
            try:
                result = compress_image_to_target(
                    str(src_path), str(out_path), target_bytes
                )
                self.root.after(0, self._on_compress_done, result, str(out_path))
            except Exception as e:
                self.root.after(0, self._on_compress_done, None, str(e))

        Thread(target=task, daemon=True).start()

    def _on_compress_done(self, result, extra):
        """压缩完成回调"""
        self._set_busy(False)
        if result is None:
            self.status_text.set(f"❌ 压缩失败：{extra}")
            messagebox.showerror("压缩失败", f"处理出错：\n{extra}")
            return

        if result["success"]:
            kb = result["final_size"] / 1024
            msg = (
                f"✅ 压缩完成！\n\n"
                f"最终大小：{kb:.1f} KB\n"
                f"迭代次数：{result['iterations']}\n\n"
                f"保存路径：{extra}"
            )
            self.status_text.set(f"✅ 压缩完成：{kb:.1f} KB → {extra}")
            messagebox.showinfo("压缩成功", msg)
        else:
            self.status_text.set(f"❌ {result['msg']}")
            messagebox.showerror("压缩失败", result["msg"])

    def _on_make_id(self, spec_name: str):
        """证件照生成按钮点击处理"""
        src = self.input_path.get()
        if not src or not os.path.isfile(src):
            messagebox.showwarning("提示", "请先选择一张照片。")
            return

        # 检查模型（首次使用证件照功能时触发）
        if not self._model_checked:
            # 先检查是否有本地模型文件
            local_model = get_model_path()
            if not local_model:
                self._set_busy(True)
                self.status_text.set("⏳ 正在检查 AI 模型...")
                self.root.update()
                ok = ensure_rembg_model(self.root)
                self._set_busy(False)
                if not ok:
                    self.status_text.set("❌ 模型不可用，证件照功能无法使用")
                    return
            self._model_checked = True

        src_path = Path(src)
        out_path = src_path.parent / f"{src_path.stem}_{spec_name}.jpg"

        self._set_busy(True)
        self.status_text.set(f"⏳ 正在生成 {spec_name}，请稍候...")

        def task():
            try:
                result = make_id_photo(str(src_path), str(out_path), spec_name)
                self.root.after(0, self._on_id_done, result, str(out_path))
            except Exception as e:
                self.root.after(0, self._on_id_done, None, str(e))

        Thread(target=task, daemon=True).start()

    def _on_id_done(self, result, extra):
        """证件照生成完成回调"""
        self._set_busy(False)
        if result is None:
            self.status_text.set(f"❌ 生成失败：{extra}")
            messagebox.showerror("生成失败", f"处理出错：\n{extra}")
            return

        if result["success"]:
            self.status_text.set(f"✅ 已生成 → {extra}")
            messagebox.showinfo("证件照生成成功", result["msg"])
        else:
            self.status_text.set(f"❌ {result['msg']}")
            messagebox.showerror("生成失败", result["msg"])

    def _set_busy(self, busy: bool):
        """设置界面繁忙状态"""
        state = tk.DISABLED if busy else tk.NORMAL
        self.btn_compress.config(state=state)
        for btn in self.id_btns.values():
            btn.config(state=state)
        if busy:
            self.progress.pack(fill=tk.X, pady=(4, 0))
            self.progress.start(10)
        else:
            self.progress.stop()
            self.progress.pack_forget()


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main():
    root = tk.Tk()
    app = PhotoToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


# ===========================================================================
# 打包成 exe 的完整步骤
# ===========================================================================
#
# 【第一步】安装依赖
#   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "rembg[cpu]" Pillow pyinstaller
#
# 【第二步】确认模型文件
#   u2net 模型（176 MB）会在首次使用证件照功能时自动下载。
#   如需离线使用，可将 u2net.onnx 文件与 photo_tool.py 放在同一目录下。
#
#   模型文件下载地址：
#   https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx
#
# 【第三步】执行打包（推荐使用 spec 文件方式，确保 rembg 完全包含）
#
#   方法一：使用 spec 文件（推荐）
#   python -m PyInstaller photo_tool.spec
#
#   方法二：命令行参数
#   python -m PyInstaller --onefile --noconsole ^
#     --hidden-import rembg ^
#     --hidden-import onnxruntime ^
#     --hidden-import pooch ^
#     --hidden-import pydantic ^
#     --collect-all rembg ^
#     photo_tool.py
#
# 注意：由于 u2net 模型高达 176 MB，不建议打包进 exe。
#       首次运行时会让用户自动下载，或手动将 u2net.onnx 放到 exe 同目录下。
# ===========================================================================