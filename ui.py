# -*- coding: utf-8 -*-
import os
import time
import math
import datetime
import threading

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction

import core


# ================= 스타일(UI) =================

def setup_app_style(app: QtWidgets.QApplication):
    app.setStyle("Fusion")

    palette = QtGui.QPalette()
    bg = QtGui.QColor(10, 13, 20)
    panel = QtGui.QColor(18, 22, 31)
    text = QtGui.QColor(235, 237, 245)
    accent = QtGui.QColor(77, 163, 255)

    palette.setColor(QtGui.QPalette.Window, bg)
    palette.setColor(QtGui.QPalette.WindowText, text)
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(15, 18, 26))
    palette.setColor(QtGui.QPalette.AlternateBase, panel)
    palette.setColor(QtGui.QPalette.ToolTipBase, panel)
    palette.setColor(QtGui.QPalette.ToolTipText, text)
    palette.setColor(QtGui.QPalette.Text, text)
    palette.setColor(QtGui.QPalette.Button, panel)
    palette.setColor(QtGui.QPalette.ButtonText, text)
    palette.setColor(QtGui.QPalette.Highlight, accent)
    palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    app.setPalette(palette)

    app.setStyleSheet("""
        QMainWindow { background-color: #0a0d14; }
        QLabel#AppTitle { color: #f5f7ff; font-size: 18px; font-weight: 600; }
        QFrame#Card {
            background-color: #111621;
            border: 1px solid #242a38;
            border-radius: 14px;
        }
        QLabel#ClockLabel { color: #f5f7ff; font-size: 40px; font-weight: 700; }
        QLabel#TimerLabel { color: #f5f7ff; font-size: 34px; font-weight: 700; }
        QLabel#TrackLabel { color: #ffffff; }
        QLabel { color: #c2c6d4; font-size: 12px; }
        QCheckBox, QRadioButton { color: #c2c6d4; font-size: 12px; }
        QLabel#TestBadge {
            background-color: #f5a623;
            color: #1b1f2a;
            font-weight: 600;
            border-radius: 9px;
            padding: 2px 6px;
        }
        QPushButton {
            background-color: #2f7ddc;
            border-radius: 8px;
            padding: 9px 16px;
            color: #f5f7ff;
            font-weight: 500;
            border: none;
        }
        QPushButton#StopButton { background-color: #d64545; }
        QPushButton#LogButton { background-color: #252b3a; }
        QPushButton:hover:enabled { background-color: #3b8af0; }
        QPushButton#StopButton:hover:enabled { background-color: #e05661; }
        QPushButton#LogButton:hover:enabled { background-color: #303648; }
        QPushButton:disabled { background-color: #353b4a; color: #8b90a0; }
        QProgressBar {
            background-color: #101521;
            border: 1px solid #242a38;
            border-radius: 6px;
            text-align: center;
            color: #e3e6f0;
            font-size: 11px;
        }
        QProgressBar::chunk { background-color: #4da3ff; border-radius: 6px; }
    """)


# ================= UI Widgets =================

class EqualizerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, bar_count=5):
        super().__init__(parent)
        self.bar_count = bar_count
        self.levels = [0.1] * bar_count
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._update_levels)
        self.setFixedHeight(40)

    def start(self):
        if not self.timer.isActive():
            self.timer.start(120)
            self.show()
            self.update()

    def stop(self):
        if self.timer.isActive():
            self.timer.stop()
        self.levels = [0.05] * self.bar_count
        self.update()

    def _update_levels(self):
        import random
        new_levels = []
        for lvl in self.levels:
            target = random.uniform(0.2, 1.0)
            new_lvl = (lvl * 0.4) + (target * 0.6)
            new_levels.append(new_lvl)
        self.levels = new_levels
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w, h = self.width(), self.height()
        margin, spacing = 6, 4
        total_spacing = spacing * (self.bar_count - 1)
        bar_width = max(4, (w - margin * 2 - total_spacing) // self.bar_count)

        base_color = QtGui.QColor(77, 163, 255)

        for i, lvl in enumerate(self.levels):
            bar_height = max(4, int(h * lvl))
            x = margin + i * (bar_width + spacing)
            y = h - bar_height
            rect = QtCore.QRectF(x, y, bar_width, bar_height)

            grad = QtGui.QLinearGradient(rect.topLeft(), rect.bottomLeft())
            grad.setColorAt(0.0, QtGui.QColor(130, 200, 255))
            grad.setColorAt(1.0, base_color)

            painter.setBrush(QtGui.QBrush(grad))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRoundedRect(rect, 3, 3)


class StatusDotWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = False
        self._phase = 0.0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setFixedSize(16, 16)

    def setActive(self, active: bool):
        self._active = active
        if active:
            if not self._timer.isActive():
                self._timer.start(60)
        else:
            if self._timer.isActive():
                self._timer.stop()
        self.update()

    def _tick(self):
        self._phase = (self._phase + 0.2) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if self._active:
            base_color = QtGui.QColor(120, 220, 160)
            scale = 1.0 + 0.15 * math.sin(self._phase)
        else:
            base_color = QtGui.QColor(130, 130, 130)
            scale = 1.0

        radius = 5 * scale
        center = QtCore.QPointF(self.width() / 2, self.height() / 2)

        grad = QtGui.QRadialGradient(center, radius)
        grad.setColorAt(0.0, QtGui.QColor(255, 255, 255))
        grad.setColorAt(0.4, base_color)
        grad.setColorAt(1.0, QtGui.QColor(15, 15, 15))

        painter.setBrush(QtGui.QBrush(grad))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(center, radius, radius)


# ================= Main Window (UI + wiring) =================

class MainWindow(QtWidgets.QMainWindow):
    MODE_AUTO = "auto"
    MODE_AUTO_TEST = "auto_test"

    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg = cfg

        ui_cfg = cfg.get("ui", {})
        self.setWindowTitle(ui_cfg.get("window_title", "YouTube Music Timer"))
        self.setMinimumSize(700, 500)

        self.always_on_top = bool(ui_cfg.get("always_on_top_default", True))
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, self.always_on_top)

        self.start_h, self.start_m = core.parse_hhmm(cfg.get("start_time", "06:50"))
        self.end_h, self.end_m = core.parse_hhmm(cfg.get("end_time", "07:50"))
        self.test_duration_min = int(cfg.get("test_duration_min", 3))

        self.is_playing = False
        self.mode = self.MODE_AUTO

        self.total_seconds = 0
        self.elapsed_seconds = 0
        self.current_track_title = ""
        self.fullscreen_done = False
        self.youtube_pid = None
        self.youtube_hwnd = None
        self.youtube_detect_time = None
        self.last_auto_start_date = None

        self.thread = None
        self.worker = None
        self.stop_event = None

        self._build_ui()
        self._create_tray_icon()

        self.countdown_timer = QtCore.QTimer(self)
        self.countdown_timer.timeout.connect(self._on_timer_tick)

        self.track_timer = QtCore.QTimer(self)
        self.track_timer.timeout.connect(self._monitor_youtube_window)
        self.track_timer.start(2000)

        self.clock_timer = QtCore.QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock_and_schedule)
        self.clock_timer.start(1000)

        shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+Alt+T"), self)
        shortcut.activated.connect(self._toggle_test_mode)

        core.write_log("========== YouTube Music Timer GUI 시작 ==========")

    # ---------- Tray ----------

    def _create_tray_icon(self):
        icon_file = self.cfg.get("ui", {}).get("icon_file", "icon.png")
        icon_path = os.path.join(core.BASE_DIR, icon_file)

        if os.path.exists(icon_path):
            icon = QtGui.QIcon(icon_path)
        else:
            icon = self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)

        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("YouTube Music Timer")
        self.tray.setVisible(True)

        self.tray_menu = QMenu()
        self.action_open = QAction("열기", self)
        self.action_hide = QAction("숨기기", self)
        self.action_refresh = QAction("상태 리프레시", self)
        self.action_log = QAction("로그 보기", self)
        self.action_exit = QAction("종료", self)

        self.tray_menu.addAction(self.action_open)
        self.tray_menu.addAction(self.action_hide)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.action_refresh)
        self.tray_menu.addAction(self.action_log)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.action_exit)

        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self._on_tray_activated)

        self.action_open.triggered.connect(self._tray_show_window)
        self.action_hide.triggered.connect(self._tray_hide_window)
        self.action_refresh.triggered.connect(self._tray_refresh_status)
        self.action_log.triggered.connect(self._open_log)
        self.action_exit.triggered.connect(self._tray_exit_app)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._tray_show_window()

    def _tray_show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_hide_window(self):
        self.hide()

    def _tray_refresh_status(self):
        msg = self.next_play_label.text()
        self.tray.showMessage("현재 상태", msg, QSystemTrayIcon.Information, 5000)

    def _tray_exit_app(self):
        if self.is_playing:
            self.stop_playback(auto=True)
        self.tray.hide()
        QtWidgets.qApp.quit()

    # ---------- UI ----------

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        header_row = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("YouTube Music Timer")
        title_label.setObjectName("AppTitle")
        title_font = QtGui.QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)

        header_row.addWidget(title_label)
        header_row.addStretch()

        right_box = QtWidgets.QHBoxLayout()
        self.test_badge = QtWidgets.QLabel("TEST")
        self.test_badge.setAlignment(QtCore.Qt.AlignCenter)
        self.test_badge.setFixedWidth(50)
        self.test_badge.setObjectName("TestBadge")
        self.test_badge.setVisible(False)

        self.always_on_top_checkbox = QtWidgets.QCheckBox("항상 위")
        self.always_on_top_checkbox.setChecked(self.always_on_top)
        self.always_on_top_checkbox.toggled.connect(self._on_toggle_topmost)

        right_box.addWidget(self.test_badge)
        right_box.addSpacing(10)
        right_box.addWidget(self.always_on_top_checkbox)

        header_row.addLayout(right_box)
        main_layout.addLayout(header_row)

        info_panel = QtWidgets.QFrame()
        info_panel.setObjectName("Card")
        info_layout = QtWidgets.QVBoxLayout(info_panel)
        info_layout.setContentsMargins(18, 14, 18, 14)
        info_layout.setSpacing(6)

        self.clock_label = QtWidgets.QLabel("--:--:--")
        self.clock_label.setObjectName("ClockLabel")
        self.clock_label.setAlignment(QtCore.Qt.AlignCenter)
        self.clock_label.setFont(QtGui.QFont("Consolas", 40, QtGui.QFont.Bold))

        self.next_play_label = QtWidgets.QLabel("재생 스케줄 정보를 불러오는 중...")
        self.next_play_label.setAlignment(QtCore.Qt.AlignCenter)
        self.next_play_label.setWordWrap(True)

        track_caption = QtWidgets.QLabel("현재 곡")
        track_caption.setAlignment(QtCore.Qt.AlignCenter)

        self.track_label = QtWidgets.QLabel("대기 중...")
        self.track_label.setObjectName("TrackLabel")
        self.track_label.setAlignment(QtCore.Qt.AlignCenter)
        self.track_label.setWordWrap(True)
        tf = QtGui.QFont()
        tf.setPointSize(11)
        tf.setBold(True)
        self.track_label.setFont(tf)

        self.status_label = QtWidgets.QLabel("대기 중")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)

        info_layout.addWidget(self.clock_label)
        info_layout.addSpacing(6)
        info_layout.addWidget(self.next_play_label)
        info_layout.addSpacing(8)
        info_layout.addWidget(track_caption)
        info_layout.addWidget(self.track_label)

        main_layout.addWidget(info_panel)

        timer_panel = QtWidgets.QFrame()
        timer_panel.setObjectName("Card")
        timer_layout = QtWidgets.QVBoxLayout(timer_panel)
        timer_layout.setContentsMargins(18, 14, 18, 14)
        timer_layout.setSpacing(10)

        self.timer_label = QtWidgets.QLabel("00:00")
        self.timer_label.setObjectName("TimerLabel")
        self.timer_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_label.setFont(QtGui.QFont("Consolas", 34, QtGui.QFont.Bold))

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)

        self.eq_widget = EqualizerWidget()
        self.eq_widget.setMinimumWidth(260)

        info_row = QtWidgets.QHBoxLayout()
        self.status_dot = StatusDotWidget()
        self.state_label = QtWidgets.QLabel("정지")
        self.running_label = QtWidgets.QLabel("대기 중")
        self.elapsed_label = QtWidgets.QLabel("경과: 00:00")
        self.total_label = QtWidgets.QLabel("")

        info_row.addWidget(self.status_dot)
        info_row.addSpacing(6)
        info_row.addWidget(self.state_label)
        info_row.addSpacing(12)
        info_row.addWidget(self.running_label)
        info_row.addStretch()
        info_row.addWidget(self.elapsed_label)
        info_row.addSpacing(12)
        info_row.addWidget(self.total_label)

        timer_layout.addWidget(self.timer_label)
        timer_layout.addWidget(self.progress_bar)
        timer_layout.addWidget(self.eq_widget, alignment=QtCore.Qt.AlignCenter)
        timer_layout.addLayout(info_row)

        main_layout.addWidget(timer_panel)

        mode_row = QtWidgets.QHBoxLayout()
        mode_row.addWidget(QtWidgets.QLabel("모드:"))
        self.radio_auto = QtWidgets.QRadioButton(f"자동 ({self.start_h:02d}:{self.start_m:02d}~{self.end_h:02d}:{self.end_m:02d})")
        self.radio_auto_test = QtWidgets.QRadioButton(f"테스트 모드 ({self.test_duration_min}분)")
        self.radio_auto.setChecked(True)
        self.radio_auto.toggled.connect(self._on_mode_changed)
        self.radio_auto_test.toggled.connect(self._on_mode_changed)
        mode_row.addWidget(self.radio_auto)
        mode_row.addWidget(self.radio_auto_test)
        mode_row.addStretch()
        main_layout.addLayout(mode_row)

        control_row = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("▶  재생 시작")
        self.start_button.setMinimumHeight(48)
        self.start_button.setMinimumWidth(160)
        self.start_button.clicked.connect(self.start_playback)

        self.stop_button = QtWidgets.QPushButton("■  정지")
        self.stop_button.setObjectName("StopButton")
        self.stop_button.setMinimumHeight(48)
        self.stop_button.setMinimumWidth(160)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_playback)

        log_button = QtWidgets.QPushButton("로그 열기")
        log_button.setObjectName("LogButton")
        log_button.setMinimumHeight(40)
        log_button.clicked.connect(self._open_log)

        control_row.addWidget(self.start_button, stretch=1)
        control_row.addSpacing(10)
        control_row.addWidget(self.stop_button, stretch=1)
        control_row.addSpacing(10)
        control_row.addWidget(log_button)

        main_layout.addLayout(control_row)

        self.eq_widget.stop()
        self.status_dot.setActive(False)
        self._reset_timer()
        self._update_schedule_status()

    # ---------- Mode / Timer ----------

    def _on_mode_changed(self):
        if self.is_playing:
            return
        if self.radio_auto.isChecked():
            self.mode = self.MODE_AUTO
            self.test_badge.setVisible(False)
        else:
            self.mode = self.MODE_AUTO_TEST
            self.test_badge.setVisible(True)
        self._reset_timer()
        self._update_schedule_status()

    def _reset_timer(self):
        if self.mode == self.MODE_AUTO_TEST:
            self.total_seconds = self.test_duration_min * 60
            self.elapsed_seconds = 0
            self.progress_bar.setMaximum(self.total_seconds)
            self.progress_bar.setValue(0)
            self.total_label.setText(f"테스트 재생: {self.test_duration_min}분")
            self._update_countdown_display()
        else:
            # 자동 모드는 “남은 시간” 기준 표시
            auto_total = ((self.end_h * 60 + self.end_m) - (self.start_h * 60 + self.start_m)) * 60
            self.progress_bar.setMaximum(max(auto_total, 1))
            self.progress_bar.setValue(0)
            self.elapsed_seconds = 0
            self.total_label.setText(f"자동 재생: {self.start_h:02d}:{self.start_m:02d} ~ {self.end_h:02d}:{self.end_m:02d}")
            self._update_auto_mode_remaining()

    def _update_countdown_display(self):
        remaining = max(self.total_seconds - self.elapsed_seconds, 0)
        rm, rs = divmod(remaining, 60)
        self.timer_label.setText(f"{rm:02d}:{rs:02d}")

        self.progress_bar.setValue(self.elapsed_seconds)
        em, es = divmod(self.elapsed_seconds, 60)
        self.elapsed_label.setText(f"경과: {em:02d}:{es:02d}")

    def _update_auto_mode_remaining(self, now=None):
        if now is None:
            now = datetime.datetime.now()

        today = now.date()
        start_dt = datetime.datetime.combine(today, datetime.time(self.start_h, self.start_m))
        end_dt = datetime.datetime.combine(today, datetime.time(self.end_h, self.end_m))

        total = int((end_dt - start_dt).total_seconds())
        if total <= 0:
            total = 1

        remaining = int((end_dt - now).total_seconds())
        if remaining < 0:
            remaining = 0

        rm, rs = divmod(remaining, 60)
        self.timer_label.setText(f"{rm:02d}:{rs:02d}")

        elapsed_from_start = int((now - start_dt).total_seconds())
        if elapsed_from_start < 0:
            elapsed_from_start = 0
        if elapsed_from_start > total:
            elapsed_from_start = total

        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(elapsed_from_start)

        em, es = divmod(max(elapsed_from_start, 0), 60)
        self.elapsed_label.setText(f"경과: {em:02d}:{es:02d}")

    def _on_timer_tick(self):
        if not self.is_playing:
            self.countdown_timer.stop()
            return
        if self.mode == self.MODE_AUTO:
            return

        self.elapsed_seconds += 1
        if self.elapsed_seconds >= self.total_seconds:
            self.elapsed_seconds = self.total_seconds
            self._update_countdown_display()
            self.countdown_timer.stop()
            self._append_status("테스트 재생 종료 - 자동 중지")
            self.stop_playback(auto=True)
        else:
            self._update_countdown_display()
            self._update_schedule_status()

    # ---------- Schedule label ----------

    def _format_timedelta_hms(self, delta: datetime.timedelta):
        if delta.total_seconds() < 0:
            delta = datetime.timedelta(seconds=0)
        total_sec = int(delta.total_seconds())
        h, rem = divmod(total_sec, 3600)
        m, s = divmod(rem, 60)
        return h, m, s

    def _update_schedule_status(self, now=None):
        if now is None:
            now = datetime.datetime.now()

        if self.mode == self.MODE_AUTO_TEST:
            if not self.is_playing and self.elapsed_seconds == 0:
                self.next_play_label.setText(
                    f"테스트 모드입니다.\n[재생 시작] 버튼을 누르면 {self.test_duration_min}분 동안 음악이 재생됩니다."
                )
            elif self.is_playing:
                remaining = max(self.total_seconds - self.elapsed_seconds, 0)
                rm, rs = divmod(remaining, 60)
                self.next_play_label.setText(f"테스트 재생 중 · 남은 시간 {rm:02d}분 {rs:02d}초")
            else:
                self.next_play_label.setText("테스트 재생이 종료되었습니다.\n다시 테스트하려면 [재생 시작] 버튼을 눌러주세요.")
            return

        today = now.date()
        start_dt = datetime.datetime.combine(today, datetime.time(self.start_h, self.start_m))
        end_dt = datetime.datetime.combine(today, datetime.time(self.end_h, self.end_m))

        if now < start_dt:
            delta = start_dt - now
            h, m, s = self._format_timedelta_hms(delta)
            text = f"다음 재생까지 {h}시간 {m}분 {s}초 남았습니다."
            detail = f"(오늘 자동 재생: {self.start_h:02d}:{self.start_m:02d} ~ {self.end_h:02d}:{self.end_m:02d})"
            self.next_play_label.setText(text + "\n" + detail)

        elif start_dt <= now < end_dt:
            delta_to_end = end_dt - now
            h, m, s = self._format_timedelta_hms(delta_to_end)
            prefix = "재생 중 · " if self.is_playing else "재생 준비 중 · "
            self.next_play_label.setText(f"{prefix}종료까지 {h}시간 {m}분 {s}초 남았습니다.")

        else:
            tomorrow = today + datetime.timedelta(days=1)
            next_start = datetime.datetime.combine(tomorrow, datetime.time(self.start_h, self.start_m))
            delta = next_start - now
            h, m, s = self._format_timedelta_hms(delta)
            self.next_play_label.setText(
                f"오늘 자동 재생이 모두 종료되었습니다.\n내일 첫 재생까지 {h}시간 {m}분 {s}초 남았습니다."
            )

    # ---------- Clock + auto start/stop ----------

    def _update_clock_and_schedule(self):
        now = datetime.datetime.now()
        self.clock_label.setText(now.strftime("%H:%M:%S"))

        if self.mode == self.MODE_AUTO:
            self._update_auto_mode_remaining(now)

            today = now.date()
            start_dt = datetime.datetime.combine(today, datetime.time(self.start_h, self.start_m))
            end_dt = datetime.datetime.combine(today, datetime.time(self.end_h, self.end_m))

            if start_dt <= now < end_dt:
                if not self.is_playing and self.last_auto_start_date != today:
                    self.last_auto_start_date = today
                    core.write_log("자동 시간 모드 - 자동 시작 시간 도달 → 재생 자동 시작")
                    self._tray_show_window()
                    self.start_playback(auto_trigger=True)

            if self.is_playing and now >= end_dt:
                self._append_status("자동 시간 모드 - 종료 시각 도달, 자동 중지")
                self.stop_playback(auto=True)

        self._update_schedule_status(now)

    # ---------- YouTube window monitor ----------

    def _monitor_youtube_window(self):
        if not self.is_playing:
            return

        hwnd, title = core.find_youtube_window(exclude_hwnd=int(self.winId()))
        if not hwnd or not title:
            return

        pid_val = QtCore.QVariant()  # dummy
        pid_dword = core.wintypes.DWORD()
        core.GetWindowThreadProcessId(hwnd, core.ctypes.byref(pid_dword))
        if pid_dword.value and pid_dword.value != self.youtube_pid:
            self.youtube_pid = pid_dword.value
            core.write_log(f"YouTube 창 PID 감지: {self.youtube_pid}")

        if not self.youtube_hwnd or int(self.youtube_hwnd) != int(hwnd):
            self.youtube_hwnd = hwnd
            self.youtube_detect_time = time.time()
            core.write_log(f"YouTube 창 핸들 감지: hwnd={hwnd}, title={title}")

        cleaned = core.clean_youtube_title(title)
        if cleaned and cleaned != self.current_track_title:
            self.current_track_title = cleaned
            self.track_label.setText(cleaned)
            self._append_status(f"현재 곡: {cleaned}")
            core.write_log(f"현재 곡 인식/갱신: {cleaned}")

        # 3초 이상 + 제목 잡힘 → 전체화면 토글(F)
        if (
            not self.fullscreen_done
            and self.youtube_hwnd
            and self.youtube_detect_time
            and (time.time() - self.youtube_detect_time) >= 3.0
            and self.current_track_title
            and self.current_track_title != self.windowTitle()
        ):
            core.write_log("전체화면 조건 만족 → F 키 전송")
            core.send_f_to_window(self.youtube_hwnd)
            self.fullscreen_done = True

    # ---------- Controls ----------

    def _append_status(self, msg: str):
        self.status_label.setText(msg)

    def _toggle_test_mode(self):
        if self.is_playing:
            QtWidgets.QMessageBox.information(self, "알림", "재생 중에는 테스트 모드를 변경할 수 없습니다.")
            return
        if self.mode == self.MODE_AUTO_TEST:
            self.radio_auto.setChecked(True)
        else:
            self.radio_auto_test.setChecked(True)

    def _open_log(self):
        if not os.path.exists(core.LOG_FILE):
            QtWidgets.QMessageBox.information(self, "알림", "로그 파일이 아직 없습니다.")
            return
        try:
            os.startfile(core.LOG_FILE)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "에러", f"로그 파일을 열 수 없습니다.\n{e}")

    def _on_toggle_topmost(self, checked: bool):
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, checked)
        self.show()

    # ---------- Play / Stop ----------

    def start_playback(self, auto_trigger: bool = False):
        if self.is_playing:
            if not auto_trigger:
                QtWidgets.QMessageBox.information(self, "알림", "이미 재생 중입니다.")
            return

        # 자동 모드일 때 수동 시작 제한(시간 전에는 막기)
        now = datetime.datetime.now()
        if self.mode == self.MODE_AUTO and not auto_trigger:
            today = now.date()
            start_dt = datetime.datetime.combine(today, datetime.time(self.start_h, self.start_m))
            end_dt = datetime.datetime.combine(today, datetime.time(self.end_h, self.end_m))
            if now < start_dt:
                QtWidgets.QMessageBox.information(self, "알림", f"자동 시간 모드는 {self.start_h:02d}:{self.start_m:02d} 이후에만 시작할 수 있습니다.")
                return
            if now >= end_dt:
                QtWidgets.QMessageBox.warning(self, "알림", f"오늘 자동 재생 종료 시각({self.end_h:02d}:{self.end_m:02d})을 지났습니다.")
                return

        # 상태 초기화
        self.current_track_title = ""
        self.track_label.setText("대기 중...")
        self.fullscreen_done = False
        self.youtube_pid = None
        self.youtube_hwnd = None
        self.youtube_detect_time = None

        self.stop_event = threading.Event()
        self.thread = QtCore.QThread(self)
        self.worker = core.PlayerWorker(self.cfg, self.stop_event)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.status.connect(self._on_worker_status)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        self.is_playing = True
        self.state_label.setText("재생 중")
        self.running_label.setText("실행 중...")
        self.running_label.setStyleSheet("color: #7bd88f;")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.eq_widget.start()
        self.status_dot.setActive(True)

        self._append_status("재생 시작")
        if self.mode == self.MODE_AUTO_TEST:
            self._reset_timer()
            self.countdown_timer.start(1000)

        self._update_schedule_status()

    def stop_playback(self, auto: bool = False):
        if not self.is_playing:
            core.write_log("stop_playback 호출됐지만 이미 정지 상태")
            return

        msg = "타이머 종료로 자동 중지" if auto else "사용자 정지"
        core.write_log(f"stop_playback 호출: {msg}")
        self._append_status(msg)

        self.is_playing = False
        self.state_label.setText("정지")
        self.running_label.setText("정지됨")
        self.running_label.setStyleSheet("")
        self.eq_widget.stop()
        self.status_dot.setActive(False)

        if self.countdown_timer.isActive():
            self.countdown_timer.stop()

        if self.stop_event:
            self.stop_event.set()

        if self.youtube_pid:
            core.kill_process_tree(self.youtube_pid)
        else:
            core.write_log("stop_playback: youtube_pid 없음 → fallback kill_profile_processes")
            core.kill_profile_processes(core.PROFILE_DIR)

        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)
        self._update_schedule_status()
        self.hide()

    # ---------- Worker callbacks ----------

    @QtCore.pyqtSlot(str, bool)
    def _on_worker_status(self, msg: str, playing: bool):
        self._append_status(msg)
        if playing and self.is_playing:
            self.state_label.setText("재생 중")

    @QtCore.pyqtSlot()
    def _on_worker_finished(self):
        core.write_log("플레이어 스레드 종료")
        self.state_label.setText("정지")
        self.running_label.setText("정지됨")
        self.running_label.setStyleSheet("")
        self.eq_widget.stop()
        self.status_dot.setActive(False)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if self.countdown_timer.isActive():
            self.countdown_timer.stop()

    # ---------- Close(X) ----------

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.is_playing:
            reply = QtWidgets.QMessageBox.question(
                self,
                "숨기기 확인",
                "현재 재생 중입니다. 음악을 중지하고 창을 숨길까요?\n(트레이 아이콘에서 다시 열 수 있습니다.)",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.No:
                event.ignore()
                return
            self.stop_playback(auto=True)
            event.ignore()
            return

        self.hide()
        event.ignore()
