#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番茄钟 - Pomodoro Timer
一个简洁的桌面番茄钟应用，使用 Python tkinter 构建。
无需额外依赖，Windows/macOS/Linux 均可运行。

功能:
  - 25分钟工作 / 5分钟短休息 / 15分钟长休息
  - 开始、暂停、重置控制
  - 完成时自动切换模式（每4个番茄后进入长休息）
  - 进度条可视化
  - 声音 + 弹窗通知
  - 会话计数
  - 窗口置顶
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# ============================================================
# Sound utilities (platform-aware)
# ============================================================

def play_notification_sound():
    """Play a notification sound. Uses winsound on Windows,
    falls back to terminal bell on other platforms."""
    if sys.platform == "win32":
        try:
            import winsound
            for _ in range(3):
                winsound.Beep(1000, 200)
                winsound.Beep(1200, 200)
            winsound.MessageBeep()
        except Exception:
            print("\a")
    else:
        # macOS / Linux: try various methods
        try:
            # macOS: use afplay
            if sys.platform == "darwin":
                os.system("afplay /System/Library/Sounds/Glass.aiff &")
            else:
                # Linux: try paplay or aplay
                os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null &")
        except Exception:
            pass
        # Always fallback to terminal bell
        print("\a")


# ============================================================
# Main Application
# ============================================================

class PomodoroApp:
    """Pomodoro Timer Application."""

    # --- Constants ---
    WORK_TIME = 25 * 60        # 25 minutes
    SHORT_BREAK = 5 * 60       # 5 minutes
    LONG_BREAK = 15 * 60       # 15 minutes

    COLOR_WORK = "#E74C3C"           # Red
    COLOR_SHORT_BREAK = "#27AE60"    # Green
    COLOR_LONG_BREAK = "#2980B9"     # Blue
    COLOR_BG = "#FAFAFA"
    COLOR_SURFACE = "#FFFFFF"
    COLOR_TEXT = "#2C3E50"
    COLOR_SUBTEXT = "#95A5A6"
    COLOR_BORDER = "#E0E0E0"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🍅 番茄钟")
        self.root.geometry("420x520")
        self.root.resizable(False, False)
        self.root.configure(bg=self.COLOR_BG)

        # --- State ---
        self.current_mode = "work"       # "work" | "short_break" | "long_break"
        self.remaining_seconds = self.WORK_TIME
        self.is_running = False
        self.completed_pomodoros = 0     # total finished work sessions
        self.after_id = None             # tkinter after() callback ID

        # --- Lookup tables ---
        self._durations = {
            "work": self.WORK_TIME,
            "short_break": self.SHORT_BREAK,
            "long_break": self.LONG_BREAK,
        }
        self._labels = {
            "work": "工作中",
            "short_break": "短休息",
            "long_break": "长休息",
        }
        self._colors = {
            "work": self.COLOR_WORK,
            "short_break": self.COLOR_SHORT_BREAK,
            "long_break": self.COLOR_LONG_BREAK,
        }

        self._build_ui()
        self._update_display()
        self._update_mode_ui()

        # Center window on screen
        self._center_window()

        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ============================================================
    # UI Construction
    # ============================================================

    def _build_ui(self):
        """Build the entire UI layout."""
        # -- Header area --
        header = tk.Frame(self.root, bg=self.COLOR_BG)
        header.pack(fill=tk.X, pady=(30, 0))

        # App icon row
        self.icon_label = tk.Label(
            header, text="🍅", font=("Segoe UI Emoji", 32),
            bg=self.COLOR_BG
        )
        self.icon_label.pack()

        # Mode indicator (colored dot + text)
        mode_row = tk.Frame(header, bg=self.COLOR_BG)
        mode_row.pack(pady=(10, 0))

        self.mode_canvas = tk.Canvas(
            mode_row, width=14, height=14,
            bg=self.COLOR_BG, highlightthickness=0
        )
        self.mode_canvas.pack(side=tk.LEFT, padx=(0, 8))
        self.mode_dot = self.mode_canvas.create_oval(
            2, 2, 14, 14, fill=self.COLOR_WORK, outline=""
        )

        self.mode_text = tk.Label(
            mode_row, text="工作中",
            font=("Microsoft YaHei", 13, "bold"),
            bg=self.COLOR_BG, fg=self.COLOR_WORK
        )
        self.mode_text.pack(side=tk.LEFT)

        # -- Timer Card (white rounded-rect effect via Frame with relief) --
        card = tk.Frame(self.root, bg=self.COLOR_SURFACE,
                        highlightbackground=self.COLOR_BORDER,
                        highlightthickness=1, padx=30, pady=25)
        card.pack(pady=(20, 10), padx=30, fill=tk.X)

        # Progress bar
        self.progress = ttk.Progressbar(
            card, orient=tk.HORIZONTAL, length=300,
            mode='determinate', maximum=self.WORK_TIME, value=0
        )
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", thickness=8,
                        troughcolor=self.COLOR_BORDER,
                        background=self.COLOR_WORK)
        self.progress.pack(pady=(0, 15))

        # Big timer digits
        self.timer_label = tk.Label(
            card, text="25:00",
            font=("Consolas", 52, "bold"),
            bg=self.COLOR_SURFACE, fg=self.COLOR_TEXT
        )
        self.timer_label.pack()

        # -- Control Buttons --
        btn_row = tk.Frame(self.root, bg=self.COLOR_BG)
        btn_row.pack(pady=(10, 0))

        self.start_btn = tk.Button(
            btn_row, text="▶  开始", command=self.start,
            font=("Microsoft YaHei", 11, "bold"),
            bg=self.COLOR_SHORT_BREAK, fg="white",
            activebackground="#1E8449", bd=0,
            width=10, padx=12, pady=6, cursor="hand2"
        )
        self.start_btn.pack(side=tk.LEFT, padx=4)

        self.pause_btn = tk.Button(
            btn_row, text="⏸  暂停", command=self.pause,
            font=("Microsoft YaHei", 11, "bold"),
            bg="#F39C12", fg="white",
            activebackground="#D68910", bd=0,
            width=10, padx=12, pady=6, cursor="hand2",
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=4)

        self.reset_btn = tk.Button(
            btn_row, text="↺  重置", command=self.reset,
            font=("Microsoft YaHei", 11, "bold"),
            bg="#95A5A6", fg="white",
            activebackground="#7F8C8D", bd=0,
            width=10, padx=12, pady=6, cursor="hand2"
        )
        self.reset_btn.pack(side=tk.LEFT, padx=4)

        # -- Mode Switcher --
        mode_label = tk.Label(
            self.root, text="切换模式",
            font=("Microsoft YaHei", 9),
            bg=self.COLOR_BG, fg=self.COLOR_SUBTEXT
        )
        mode_label.pack(pady=(20, 5))

        mode_btns = tk.Frame(self.root, bg=self.COLOR_BG)
        mode_btns.pack()

        self.work_btn = tk.Button(
            mode_btns, text="💼 工作", command=lambda: self.switch_mode("work"),
            font=("Microsoft YaHei", 10),
            bg=self.COLOR_WORK, fg="white",
            activebackground="#C0392B", bd=0,
            width=10, padx=10, pady=5, cursor="hand2"
        )
        self.work_btn.pack(side=tk.LEFT, padx=3)

        self.short_btn = tk.Button(
            mode_btns, text="☕ 短休", command=lambda: self.switch_mode("short_break"),
            font=("Microsoft YaHei", 10),
            bg=self.COLOR_SHORT_BREAK, fg="white",
            activebackground="#1E8449", bd=0,
            width=10, padx=10, pady=5, cursor="hand2"
        )
        self.short_btn.pack(side=tk.LEFT, padx=3)

        self.long_btn = tk.Button(
            mode_btns, text="🌴 长休", command=lambda: self.switch_mode("long_break"),
            font=("Microsoft YaHei", 10),
            bg=self.COLOR_LONG_BREAK, fg="white",
            activebackground="#1F6EA1", bd=0,
            width=10, padx=10, pady=5, cursor="hand2"
        )
        self.long_btn.pack(side=tk.LEFT, padx=3)

        # -- Bottom Bar --
        bottom = tk.Frame(self.root, bg=self.COLOR_BG)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 15))

        self.session_label = tk.Label(
            bottom, text="已完成: 0 个番茄 🍅",
            font=("Microsoft YaHei", 10),
            bg=self.COLOR_BG, fg=self.COLOR_SUBTEXT
        )
        self.session_label.pack(side=tk.LEFT, padx=(30, 0))

        self.top_var = tk.BooleanVar(value=False)
        self.top_check = tk.Checkbutton(
            bottom, text="📌 窗口置顶", variable=self.top_var,
            command=self._toggle_always_on_top,
            font=("Microsoft YaHei", 9),
            bg=self.COLOR_BG, fg=self.COLOR_SUBTEXT,
            activebackground=self.COLOR_BG,
            selectcolor=self.COLOR_BG, cursor="hand2"
        )
        self.top_check.pack(side=tk.RIGHT, padx=(0, 30))

    # ============================================================
    # Helpers
    # ============================================================

    @staticmethod
    def _fmt(seconds: int) -> str:
        """Format seconds as MM:SS."""
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _center_window(self):
        """Center the window on the primary screen."""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def _update_display(self):
        """Refresh timer digits and progress bar."""
        self.timer_label.config(text=self._fmt(self.remaining_seconds))
        total = self._durations[self.current_mode]
        elapsed = total - self.remaining_seconds
        self.progress.config(maximum=total, value=elapsed)

    def _update_mode_ui(self):
        """Sync mode indicator dot, label, progress color."""
        c = self._colors[self.current_mode]
        label = self._labels[self.current_mode]

        self.mode_canvas.itemconfig(self.mode_dot, fill=c)
        self.mode_text.config(text=label, fg=c)

        # Tint the progress bar
        style = ttk.Style()
        style.configure("TProgressbar", background=c)

        # Highlight the active mode button by lowering others
        self._set_btn_active(self.work_btn, self.current_mode == "work", self.COLOR_WORK)
        self._set_btn_active(self.short_btn, self.current_mode == "short_break", self.COLOR_SHORT_BREAK)
        self._set_btn_active(self.long_btn, self.current_mode == "long_break", self.COLOR_LONG_BREAK)

    @staticmethod
    def _set_btn_active(btn, active: bool, color: str):
        """Dim or highlight a mode-switch button."""
        if active:
            btn.config(bg=color, fg="white")
        else:
            btn.config(bg="#BDC3C7", fg="white")

    def _toggle_always_on_top(self):
        self.root.attributes("-topmost", self.top_var.get())

    # ============================================================
    # Timer Logic
    # ============================================================

    def start(self):
        """Start or resume the countdown."""
        if self.is_running:
            return
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED, bg="#A8E6CF")
        self.pause_btn.config(state=tk.NORMAL, bg="#F39C12")
        self._schedule_tick()

    def pause(self):
        """Pause the countdown."""
        if not self.is_running:
            return
        self.is_running = False
        self._cancel_tick()
        self.start_btn.config(state=tk.NORMAL, bg=self.COLOR_SHORT_BREAK)
        self.pause_btn.config(state=tk.DISABLED, bg="#F9E79F")

    def reset(self):
        """Reset to the full duration of the current mode."""
        self.pause()
        self.remaining_seconds = self._durations[self.current_mode]
        self._update_display()

    def _schedule_tick(self):
        """Schedule the next tick via tkinter's after()."""
        self.after_id = self.root.after(1000, self._tick)

    def _cancel_tick(self):
        """Cancel a pending tick callback."""
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _tick(self):
        """Called every second while the timer is running."""
        if not self.is_running:
            return

        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self._update_display()
            self._schedule_tick()
        else:
            # Timer reached zero
            self.is_running = False
            self.start_btn.config(state=tk.NORMAL, bg=self.COLOR_SHORT_BREAK)
            self.pause_btn.config(state=tk.DISABLED, bg="#F9E79F")
            self._on_complete()

    # ============================================================
    # Mode Switching
    # ============================================================

    def switch_mode(self, mode: str):
        """Manually switch to a new mode, resetting the timer."""
        self.pause()
        self.current_mode = mode
        self.remaining_seconds = self._durations[mode]
        self._update_mode_ui()
        self._update_display()

    def _on_complete(self):
        """Called when the timer reaches 0:00."""
        play_notification_sound()

        if self.current_mode == "work":
            self.completed_pomodoros += 1
            self.session_label.config(
                text=f"已完成: {self.completed_pomodoros} 个番茄 🍅"
            )

            # Every 4 work sessions → long break, otherwise short break
            if self.completed_pomodoros % 4 == 0:
                next_mode = "long_break"
                msg = "🎉 太棒了！4 个番茄完成，享受一个长休息吧！"
            else:
                next_mode = "short_break"
                msg = "✅ 工作时间结束！起来活动一下吧。"
        else:
            next_mode = "work"
            msg = "⏰ 休息时间结束！准备好开始新的番茄了吗？"

        # Bring window to front
        self.root.lift()
        self.root.focus_force()

        # Switch to next mode
        self.switch_mode(next_mode)

        # Show notification dialog (deferred so UI updates first)
        self.root.after(300, lambda: messagebox.showinfo(
            "番茄钟 ⏰", msg, parent=self.root
        ))

    # ============================================================
    # Cleanup
    # ============================================================

    def _on_close(self):
        """Clean up and exit."""
        self._cancel_tick()
        self.root.destroy()

    def run(self):
        """Launch the application main loop."""
        self.root.mainloop()


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    app = PomodoroApp()
    app.run()
