# core.py

# Core utility functions and Windows API interactions
import os
import sys
import time
import json
import math
import random
import datetime
import subprocess
import threading
import ctypes
from ctypes import wintypes

# Third-party modules
import psutil
from PyQt5 import QtCore


# 경로 설정
TEMP_DIR = os.getenv("TEMP") or os.getcwd()
PROFILE_DIR = os.path.join(TEMP_DIR, "MusicBotProfile")
LOG_FILE = os.path.join(TEMP_DIR, "MusicBot_Debug.txt") # 로그 파일 경로 tmp에 있음

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))


# 로그 기록
def write_log(msg: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


# 설정 파일 로드
def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# 시간 문자열 "HH:MM" 파싱
def parse_hhmm(hhmm: str) -> tuple[int, int]:
    hh, mm = hhmm.strip().split(":")
    return int(hh), int(mm)

# 트랙 URL 무작위 선택
def pick_track_url(cfg: dict) -> str:
    tracks = cfg.get("tracks") or []
    if not tracks:
        return ""
    return random.choice(tracks)



# Windows API 함수 로드
user32 = ctypes.windll.user32

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM) 

# 함수 프로토타입 설정
EnumWindows = user32.EnumWindows 
GetWindowTextLengthW = user32.GetWindowTextLengthW # 윈도우 제목 길이
GetWindowTextW = user32.GetWindowTextW # 윈도우 제목 얻기
IsWindowVisible = user32.IsWindowVisible # 창이 보이는지
SetForegroundWindow = user32.SetForegroundWindow # 창 포그라운드로
ShowWindow = user32.ShowWindow # 창 보이기/숨기기
GetWindowThreadProcessId = user32.GetWindowThreadProcessId # 프로세스 ID 얻기

# ShowWindow 명령어 
SW_RESTORE = 9 

# 키보드 메시지 
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_F = 0x46


# 유튜브 창 제목 정리
def clean_youtube_title(raw: str) -> str:
    """윈도우 제목에서 유튜브 곡 이름만 추출"""
    if not raw:
        return ""
    for sep in [
        " - YouTube Music",
        " - YouTube",
        " - Google Chrome",
        " - Microsoft Edge",
        " - Brave",
    ]:
        if sep in raw:
            raw = raw.split(sep)[0]
    return raw.strip()

# 유튜브 창 찾기
def find_youtube_window(exclude_hwnd=None):

    found_hwnd = [None]
    found_title = [""]

    def enum_proc(hwnd, lParam):
        if exclude_hwnd and int(hwnd) == int(exclude_hwnd):
            return True

        if not IsWindowVisible(hwnd):
            return True

        length = GetWindowTextLengthW(hwnd)
        if length == 0:
            return True

        buf = ctypes.create_unicode_buffer(length + 1)
        GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value or ""
        if not title:
            return True

        if "youtube" in title.lower():
            found_hwnd[0] = hwnd
            found_title[0] = title
            return False

        return True

    EnumWindows(WNDENUMPROC(enum_proc), 0)
    return found_hwnd[0], found_title[0]

# F 키 메시지 보내기 (전체화면)
def send_f_to_window(hwnd):
    """특정 창에 직접 F 키 메시지 전달(PostMessage)"""
    if not hwnd:
        return
    try:
        ShowWindow(hwnd, SW_RESTORE)
        try:
            SetForegroundWindow(hwnd)
        except Exception:
            pass

        user32.PostMessageW(hwnd, WM_KEYDOWN, VK_F, 0)
        time.sleep(0.05)
        user32.PostMessageW(hwnd, WM_KEYUP, VK_F, 0)
        write_log("유튜브 창에 F 키 메시지(PostMessage) 전송 시도")
    except Exception as e:
        write_log(f"F키 전송 실패: {e}")


# ================== Process kill ==================
# 프로필 디렉토리 포함 프로세스 종료 (fallback)
def kill_profile_processes(profile_dir: str = PROFILE_DIR):
    """profile_dir이 cmdline에 포함된 프로세스 종료 (fallback)"""
    target = profile_dir.lower()
    write_log(f"[fallback] 프로필 프로세스 정밀 종료 시도: {profile_dir}")

    killed = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info.get("cmdline") or []
            cmdline_str = " ".join(cmdline).lower()
            if target in cmdline_str:
                write_log(f"  종료 대상 PID={proc.pid}, name={proc.info.get('name')}")
                try:
                    proc.kill()
                    killed.append(proc.pid)
                except Exception as e:
                    write_log(f"  종료 실패 PID={proc.pid}: {e}")
        except Exception:
            continue

    write_log(f"  종료된 PID 목록: {killed}")
    write_log("[fallback] 프로필 프로세스 정밀 종료 완료")

# 루트 PID 기준으로 자식까지 종료 (듀온 다 꺼짐)
def kill_process_tree(root_pid: int):
    """루트 PID 기준으로 자식까지 종료"""
    if not root_pid:
        write_log("kill_process_tree: root_pid 없음")
        return

    try:
        root = psutil.Process(root_pid)
    except psutil.NoSuchProcess:
        write_log(f"kill_process_tree: PID {root_pid} 프로세스 없음")
        return
    except Exception as e:
        write_log(f"kill_process_tree: PID {root_pid} 접근 실패: {e}")
        return

    children = root.children(recursive=True)
    child_pids = [c.pid for c in children]

    for p in children:
        try:
            p.kill()
        except Exception as e:
            write_log(f"kill_process_tree: 자식 PID {p.pid} kill 실패: {e}")

    try:
        root.kill()
    except Exception as e:
        write_log(f"kill_process_tree: 루트 PID {root_pid} kill 실패: {e}")

    try:
        os.system(f"taskkill /F /T /PID {root_pid}")
    except Exception as e:
        write_log(f"kill_process_tree: taskkill 실패: {e}")

    write_log(f"kill_process_tree: 루트 {root_pid}, 자식 {child_pids} 종료 시도 완료")


# ==================  Chrome launch ==================
# 브라우저 실행 및 모니터링
class PlayerWorker(QtCore.QObject):
    status = QtCore.pyqtSignal(str, bool)
    finished = QtCore.pyqtSignal()

    def __init__(self, cfg: dict, stop_event: threading.Event, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.stop_event = stop_event
        self.proc = None

    def _emit(self, msg: str, playing: bool):
        write_log(msg)
        self.status.emit(msg, playing)

    @QtCore.pyqtSlot()
    def run(self):
        browser_path = self.cfg.get("browser_path", "")
        if not browser_path or not os.path.exists(browser_path):
            self._emit(f"브라우저 경로 없음: {browser_path}", False)
            self.finished.emit()
            return

        url = pick_track_url(self.cfg)
        if not url:
            self._emit("tracks 설정이 비어있습니다(config.json).", False)
            self.finished.emit()
            return

        try:
            self._emit(f"재생 URL: {url}", True)

            cmd = [
                browser_path,
                f"--user-data-dir={PROFILE_DIR}",
                "--new-window",
                "--start-maximized",
                "--autoplay-policy=no-user-gesture-required",
                url,
            ]
            self._emit(f"브라우저 실행 명령: {' '.join(cmd)}", True)

            self.proc = subprocess.Popen(cmd)
            self._emit(f"브라우저 실행 (PID: {self.proc.pid})", True)
            self._emit("브라우저 실행 완료, 유튜브 로딩은 GUI에서 모니터링", True)

            while not self.stop_event.is_set():
                time.sleep(1)

            self._emit("재생 루프 종료 요청 수신", False)

        except Exception as e:
            self._emit(f"에러 발생: {e}", False)

        finally:
            try:
                if self.proc and self.proc.poll() is None:
                    try:
                        os.system(f"taskkill /F /T /PID {self.proc.pid}")
                    except Exception as e:
                        write_log(f"worker 내 taskkill 실패: {e}")
                kill_profile_processes(PROFILE_DIR)
            except Exception:
                pass

            self.finished.emit()
