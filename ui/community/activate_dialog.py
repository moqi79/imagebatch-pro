"""升级激活对话框。

三步流程：
1. 选择版本 -> 生成订单 -> 显示支付信息
2. 用户扫码/转账付款
3. 输入支付确认码 -> 本地校验 -> 自动激活
"""
import tkinter as tk
from tkinter import ttk, messagebox

from config import __version__
from core.payment import (
    generate_order, confirm_payment, PRICING,
    format_order_text, get_pending_orders,
)
from core.license import get_license_manager


class ActivateDialog(tk.Toplevel):
    """升级激活对话框。"""

    def __init__(self, master):
        super().__init__(master)
        self.title("升级专业版")
        self.resizable(False, False)
        self.configure(padx=24, pady=20)
        self.order = None

        self._center(480, 520)
        self._build_ui()
        self.transient(master)
        self.grab_set()

    def _center(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 3
        self.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        lm = get_license_manager()

        # ---- 状态区 ----
        status_frame = ttk.LabelFrame(self, text="当前授权状态", padding=10)
        status_frame.pack(fill="x", pady=(0, 10))
        tk.Label(status_frame, text=lm.summary(), font=("", 10),
                 fg="#333333").pack(anchor="w")

        if lm.is_activated:
            ttk.Button(status_frame, text="撤销激活",
                       command=self._deactivate).pack(anchor="w", pady=(6, 0))

        # ---- 版本选择 ----
        ver_frame = ttk.LabelFrame(self, text="第 1 步：选择版本", padding=10)
        ver_frame.pack(fill="x", pady=(0, 10))

        for ed, info in PRICING.items():
            row = ttk.Frame(ver_frame)
            row.pack(fill="x", pady=2)
            ttk.Radiobutton(row, variable=self._var_edition(ed),
                            value=ed,
                            text=f"{info['name']}  {info['price_text']}"
                            ).pack(side="left")

        self.var_edition = tk.StringVar(value="pro")
        for ed in PRICING:
            pass  # radiobuttons 绑定 self.var_edition

        # 重新创建带正确 variable 的 radiobutton
        for w in ver_frame.winfo_children():
            for child in w.winfo_children():
                child.destroy()
        for ed, info in PRICING.items():
            row = ttk.Frame(ver_frame)
            row.pack(fill="x", pady=2)
            ttk.Radiobutton(row, variable=self.var_edition, value=ed,
                            text=f"{info['name']}  {info['price_text']}").pack(side="left")

        ttk.Button(ver_frame, text="生成支付订单",
                   command=self._create_order).pack(pady=(8, 0))

        # ---- 订单信息 ----
        self.order_frame = ttk.LabelFrame(self, text="第 2 步：扫码付款", padding=10)
        self.order_frame.pack(fill="x", pady=(0, 10))
        self.order_text = tk.Text(self.order_frame, height=7, width=52,
                                  bg="#f5f5f5", relief="flat", wrap="word")
        self.order_text.pack(fill="x")
        self.order_text.configure(state="disabled")

        # ---- 确认激活 ----
        confirm_frame = ttk.LabelFrame(self, text="第 3 步：输入支付确认码激活", padding=10)
        confirm_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(confirm_frame, text="支付确认码:").pack(anchor="w")
        self.var_confirm = tk.StringVar()
        entry = ttk.Entry(confirm_frame, textvariable=self.var_confirm,
                         width=40)
        entry.pack(fill="x", pady=(2, 4))
        ttk.Label(confirm_frame,
                  text="格式: PAY-XXXXXXXX-P-XXXXXXXX\n（付款后从开发者或发卡平台获取）",
                  foreground="#999999", font=("", 8)).pack(anchor="w")

        btn_row = ttk.Frame(confirm_frame)
        btn_row.pack(pady=(6, 0))
        ttk.Button(btn_row, text="确认支付并激活",
                   command=self._confirm_payment).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="查看待支付订单",
                   command=self._show_pending).pack(side="left")

        # ---- 底部 ----
        ttk.Button(self, text="关闭", command=self.destroy).pack(side="right")

    def _var_edition(self, _):
        return self.var_edition if hasattr(self, "var_edition") else tk.StringVar()

    def _create_order(self):
        edition = self.var_edition.get()
        if edition not in PRICING:
            messagebox.showwarning("提示", "请选择版本", parent=self)
            return
        self.order = generate_order(edition)
        text = format_order_text(self.order)
        text += f"\n\n支付确认码: {self.order['confirm_code']}"
        text += "\n\n请扫码或转账付款后，将确认码输入下方激活。"

        self.order_text.configure(state="normal")
        self.order_text.delete("1.0", "end")
        self.order_text.insert("1.0", text)
        self.order_text.configure(state="disabled")

        # 自动填入确认码方便用户检查
        self.var_confirm.set(self.order["confirm_code"])

    def _confirm_payment(self):
        code = self.var_confirm.get().strip()
        if not code:
            messagebox.showwarning("提示", "请输入支付确认码", parent=self)
            return

        success, message, _key = confirm_payment(code)
        if success:
            messagebox.showinfo("激活成功", message, parent=self)
            self.destroy()
        else:
            messagebox.showerror("激活失败", message, parent=self)

    def _show_pending(self):
        orders = get_pending_orders()
        if not orders:
            messagebox.showinfo("待支付订单", "暂无待支付订单", parent=self)
            return
        lines = []
        for o in orders[-5:]:
            lines.append(format_order_text(o))
            lines.append("-" * 40)
        messagebox.showinfo("待支付订单", "\n".join(lines), parent=self)

    def _deactivate(self):
        if messagebox.askyesno("确认", "确定撤销当前授权？将回到社区版。",
                               parent=self):
            get_license_manager().deactivate()
            messagebox.showinfo("已撤销", "已回到社区版。", parent=self)
            self.destroy()
