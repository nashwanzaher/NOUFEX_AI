from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    handle: int
    title: str
    class_name: str
    is_visible: bool
    rect: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "handle": self.handle,
            "title": self.title,
            "class_name": self.class_name,
            "is_visible": self.is_visible,
            "rect": self.rect,
        }


@dataclass
class ScreenInfo:
    width: int
    height: int
    dpi_scale: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"width": self.width, "height": self.height, "dpi_scale": self.dpi_scale}


@dataclass
class ProcessInfo:
    pid: int
    name: str
    window_title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"pid": self.pid, "name": self.name, "window_title": self.window_title}


class ComputerService:
    """Desktop computer control service.
    
    Provides window management, screen capture, mouse/keyboard automation,
    and process control. Mirrors OpenClaw's computer-use capabilities.
    """

    def __init__(self) -> None:
        self._os = platform.system().lower()
        self._screenshot_dir = Path(tempfile.gettempdir()) / "noufex_screenshots"
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)

    # ── Window Management ──────────────────────────────────────────────

    def list_windows(self) -> list[dict[str, Any]]:
        """List all visible windows on the desktop."""
        return self._list_windows_impl()

    def _list_windows_impl(self) -> list[dict[str, Any]]:
        if self._os == "windows":
            return self._list_windows_win32()
        elif self._os == "linux":
            return self._list_windows_x11()
        elif self._os == "darwin":
            return self._list_windows_macos()
        return []

    def _list_windows_win32(self) -> list[dict[str, Any]]:
        try:
            import win32gui
            import win32con
        except ImportError:
            logger.warning("pywin32 not installed. Install with: pip install pywin32")
            return []

        windows: list[dict[str, Any]] = []

        def _enum_callback(hwnd: int, _result: list) -> None:
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd) or ""
            if not title:
                return
            cls_name = win32gui.GetClassName(hwnd)
            try:
                rect = win32gui.GetWindowRect(hwnd)
                rect_dict = {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3]}
            except Exception:
                rect_dict = None
            windows.append(
                WindowInfo(
                    handle=hwnd,
                    title=title,
                    class_name=cls_name,
                    is_visible=True,
                    rect=rect_dict,
                ).to_dict()
            )

        win32gui.EnumWindows(_enum_callback, windows)
        return windows

    def _list_windows_x11(self) -> list[dict[str, Any]]:
        try:
            import Xlib.display
        except ImportError:
            logger.warning("python-xlib not installed")
            return []

        try:
            display = Xlib.display.Display()
            root = display.screen().root
            window_ids = root.get_full_property(
                display.intern_atom("_NET_CLIENT_LIST_STACKING"),
                Xlib.X.AnyPropertyType,
            )
            if not window_ids:
                return []
            windows = []
            for wid in window_ids.value:
                try:
                    win = display.create_resource_object("window", wid)
                    title_atom = display.intern_atom("_NET_WM_NAME")
                    title = win.get_full_property(title_atom, 0)
                    title_str = title.value.decode("utf-8") if title else ""
                    if title_str:
                        windows.append(
                            WindowInfo(
                                handle=wid,
                                title=title_str,
                                class_name="",
                                is_visible=True,
                            ).to_dict()
                        )
                except Exception:
                    continue
            display.close()
            return windows
        except Exception as e:
            logger.error("X11 window listing failed: %s", e)
            return []

    def _list_windows_macos(self) -> list[dict[str, Any]]:
        try:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to get name of every process whose visible is true',
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return []
            names = [n.strip() for n in result.stdout.split(",") if n.strip()]
            return [
                WindowInfo(handle=hash(n), title=n, class_name="", is_visible=True).to_dict()
                for n in names
            ]
        except Exception as e:
            logger.error("macOS window listing failed: %s", e)
            return []

    def focus_window(self, identifier: str | int) -> dict[str, Any]:
        """Focus/bring window to foreground. identifier=window title or handle."""
        if self._os == "windows":
            return self._focus_window_win32(identifier)
        elif self._os == "linux":
            return self._focus_window_x11(identifier)
        elif self._os == "darwin":
            return self._focus_window_macos(identifier)
        return {"success": False, "error": f"Unsupported OS: {self._os}"}

    def _focus_window_win32(self, identifier: str | int) -> dict[str, Any]:
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"success": False, "error": "pywin32 not installed"}

        target_hwnd: int | None = None
        if isinstance(identifier, int):
            target_hwnd = identifier
        else:
            windows = self._list_windows_win32()
            for w in windows:
                if identifier.lower() in w["title"].lower():
                    target_hwnd = w["handle"]
                    break

        if target_hwnd is None:
            return {"success": False, "error": f"Window '{identifier}' not found"}

        try:
            if win32gui.IsIconic(target_hwnd):
                win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(target_hwnd)
            return {"success": True, "window": identifier, "handle": target_hwnd}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _focus_window_x11(self, identifier: str | int) -> dict[str, Any]:
        try:
            import Xlib.display
        except ImportError:
            return {"success": False, "error": "python-xlib not installed"}

        try:
            display = Xlib.display.Display()
            root = display.screen().root
            window_ids = root.get_full_property(
                display.intern_atom("_NET_CLIENT_LIST_STACKING"),
                Xlib.X.AnyPropertyType,
            )
            if not window_ids:
                return {"success": False, "error": "No windows found"}

            target_wid: int | None = None
            if isinstance(identifier, int):
                target_wid = identifier
            else:
                for wid in window_ids.value:
                    win = display.create_resource_object("window", wid)
                    title_atom = display.intern_atom("_NET_WM_NAME")
                    title = win.get_full_property(title_atom, 0)
                    title_str = title.value.decode("utf-8") if title else ""
                    if identifier.lower() in title_str.lower():
                        target_wid = wid
                        break

            if target_wid is None:
                display.close()
                return {"success": False, "error": f"Window '{identifier}' not found"}

            root.set_active_window(target_wid)
            display.sync()
            display.close()
            return {"success": True, "window": identifier, "handle": target_wid}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _focus_window_macos(self, identifier: str | int) -> dict[str, Any]:
        app_name = str(identifier)
        try:
            subprocess.run(
                ["osascript", "-e", f'tell application "{app_name}" to activate'],
                check=True,
                timeout=5,
            )
            return {"success": True, "window": app_name}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout activating window"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": str(e)}

    def move_window(
        self, identifier: str | int, x: int, y: int, width: int | None = None, height: int | None = None
    ) -> dict[str, Any]:
        """Move and optionally resize a window."""
        if self._os != "windows":
            return {"success": False, "error": "Window move/resize only supported on Windows"}
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"success": False, "error": "pywin32 not installed"}

        target_hwnd: int | None = None
        if isinstance(identifier, int):
            target_hwnd = identifier
        else:
            windows = self._list_windows_win32()
            for w in windows:
                if identifier.lower() in w["title"].lower():
                    target_hwnd = w["handle"]
                    break

        if target_hwnd is None:
            return {"success": False, "error": f"Window '{identifier}' not found"}

        try:
            if width and height:
                win32gui.MoveWindow(target_hwnd, x, y, width, height, True)
            else:
                win32gui.SetWindowPos(
                    target_hwnd, 0, x, y, 0, 0,
                    win32con.SWP_NOSIZE | win32con.SWP_NOZORDER,
                )
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_window(self, target: str) -> dict[str, Any]:
        """Open a window by launching an application or file."""
        try:
            if self._os == "windows":
                os.startfile(target)
            elif self._os == "linux":
                subprocess.Popen(["xdg-open", target], start_new_session=True)
            elif self._os == "darwin":
                subprocess.Popen(["open", target], start_new_session=True)
            return {"success": True, "target": target}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close_window(self, identifier: str | int) -> dict[str, Any]:
        """Close a window."""
        if self._os == "windows":
            return self._close_window_win32(identifier)
        return self._close_window_ps(identifier)

    def _close_window_win32(self, identifier: str | int) -> dict[str, Any]:
        try:
            import win32gui
            import win32con
        except ImportError:
            return {"success": False, "error": "pywin32 not installed"}

        target_hwnd: int | None = None
        if isinstance(identifier, int):
            target_hwnd = identifier
        else:
            windows = self._list_windows_win32()
            for w in windows:
                if identifier.lower() in w["title"].lower():
                    target_hwnd = w["handle"]
                    break

        if target_hwnd is None:
            return {"success": False, "error": f"Window '{identifier}' not found"}

        try:
            win32gui.PostMessage(target_hwnd, win32con.WM_CLOSE, 0, 0)
            return {"success": True, "window": identifier}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _close_window_ps(self, identifier: str | int) -> dict[str, Any]:
        try:
            import psutil
        except ImportError:
            return {"success": False, "error": "psutil not installed"}

        app_name = str(identifier).replace(".exe", "")
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if app_name.lower() in proc.info["name"].lower():
                    proc.terminate()
                    return {"success": True, "process": proc.info["name"]}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {"success": False, "error": f"Process '{identifier}' not found"}

    def get_active_window(self) -> dict[str, Any]:
        """Get the currently focused window."""
        if self._os == "windows":
            try:
                import win32gui
                hwnd = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(hwnd) or ""
                cls_name = win32gui.GetClassName(hwnd)
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    rect_dict = {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3]}
                except Exception:
                    rect_dict = None
                return WindowInfo(
                    handle=hwnd, title=title, class_name=cls_name,
                    is_visible=True, rect=rect_dict,
                ).to_dict()
            except ImportError:
                return {"handle": -1, "title": "", "error": "pywin32 not installed"}
        return {"handle": -1, "title": "", "os": self._os}

    # ── Screen Capture ─────────────────────────────────────────────────

    def get_screen_info(self) -> dict[str, Any]:
        """Get screen resolution and info."""
        try:
            from PIL import ImageGrab
            screen = ImageGrab.grab()
            width, height = screen.size
            return ScreenInfo(width=width, height=height).to_dict()
        except ImportError:
            return ScreenInfo(width=0, height=0).to_dict()

    def screenshot(self, region: list[int] | None = None) -> dict[str, Any]:
        """Take a screenshot. Returns base64 image data.
        
        Args:
            region: [left, top, right, bottom] or None for full screen
        """
        try:
            from PIL import ImageGrab
            import base64
            from io import BytesIO

            if region and len(region) == 4:
                img = ImageGrab.grab(bbox=tuple(region))
            else:
                img = ImageGrab.grab()

            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            filename = f"screenshot_{uuid4().hex[:8]}.png"
            filepath = self._screenshot_dir / filename
            img.save(str(filepath))

            return {
                "success": True,
                "data": img_b64,
                "format": "png",
                "width": img.width,
                "height": img.height,
                "filepath": str(filepath),
            }
        except ImportError:
            return {"success": False, "error": "Pillow not installed. Install with: pip install Pillow"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def screenshot_to_data(self, region: list[int] | None = None) -> tuple[str, int, int] | None:
        """Take screenshot and return (base64, width, height). Used by LLM vision."""
        try:
            from PIL import ImageGrab
            import base64
            from io import BytesIO

            if region and len(region) == 4:
                img = ImageGrab.grab(bbox=tuple(region))
            else:
                img = ImageGrab.grab()

            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8"), img.width, img.height
        except Exception:
            return None

    # ── Mouse Control ──────────────────────────────────────────────────

    def mouse_move(self, x: int, y: int) -> dict[str, Any]:
        """Move mouse to absolute position (x, y)."""
        try:
            import pyautogui
            pyautogui.moveTo(x, y)
            return {"success": True, "x": x, "y": y}
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}

    def mouse_click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> dict[str, Any]:
        """Click at position (x, y)."""
        try:
            import pyautogui
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            return {"success": True, "x": x, "y": y, "button": button, "clicks": clicks}
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}

    def mouse_double_click(self, x: int, y: int) -> dict[str, Any]:
        """Double-click at position."""
        return self.mouse_click(x, y, clicks=2)

    def mouse_right_click(self, x: int, y: int) -> dict[str, Any]:
        """Right-click at position."""
        return self.mouse_click(x, y, button="right")

    def mouse_drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> dict[str, Any]:
        """Drag from (x1,y1) to (x2,y2)."""
        try:
            import pyautogui
            pyautogui.moveTo(x1, y1)
            pyautogui.drag(x2 - x1, y2 - y1, duration=duration)
            return {"success": True, "from": [x1, y1], "to": [x2, y2]}
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}

    def mouse_scroll(self, clicks: int, x: int | None = None, y: int | None = None) -> dict[str, Any]:
        """Scroll. Positive=up, negative=down."""
        try:
            import pyautogui
            if x is not None and y is not None:
                pyautogui.scroll(clicks, x=x, y=y)
            else:
                pyautogui.scroll(clicks)
            return {"success": True, "clicks": clicks}
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}

    def mouse_position(self) -> dict[str, Any]:
        """Get current mouse position."""
        try:
            import pyautogui
            x, y = pyautogui.position()
            return {"success": True, "x": x, "y": y}
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}

    # ── Keyboard Control ───────────────────────────────────────────────

    def keyboard_type(self, text: str, interval: float = 0.05) -> dict[str, Any]:
        """Type text at current focus."""
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=interval)
            return {"success": True, "characters": len(text)}
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}

    def keyboard_hotkey(self, *keys: str) -> dict[str, Any]:
        """Press a hotkey combination. e.g. hotkey('ctrl', 'c') for copy."""
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            return {"success": True, "keys": list(keys)}
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}

    def keyboard_press(self, key: str) -> dict[str, Any]:
        """Press and release a single key."""
        try:
            import pyautogui
            pyautogui.press(key)
            return {"success": True, "key": key}
        except ImportError:
            return {"success": False, "error": "pyautogui not installed"}

    # ── Process Management ─────────────────────────────────────────────

    def list_processes(self) -> list[dict[str, Any]]:
        """List running processes."""
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    pinfo = proc.info
                    processes.append(
                        ProcessInfo(pid=pinfo["pid"], name=pinfo["name"]).to_dict()
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return sorted(processes, key=lambda p: p["name"].lower())[:200]
        except ImportError:
            return []

    def kill_process(self, pid_or_name: int | str) -> dict[str, Any]:
        """Kill a process by PID or name."""
        try:
            import psutil
        except ImportError:
            return {"success": False, "error": "psutil not installed"}

        try:
            if isinstance(pid_or_name, int):
                proc = psutil.Process(pid_or_name)
                proc.terminate()
                return {"success": True, "pid": pid_or_name}
            else:
                killed = []
                for proc in psutil.process_iter(["pid", "name"]):
                    try:
                        if pid_or_name.lower() in proc.info["name"].lower():
                            proc.terminate()
                            killed.append(proc.info["pid"])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                return {"success": len(killed) > 0, "killed": killed}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── System Info ────────────────────────────────────────────────────

    def get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "processor": platform.processor(),
        }
        try:
            import psutil
            info["cpu_count"] = psutil.cpu_count()
            info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            info["memory_total_gb"] = round(mem.total / (1024**3), 2)
            info["memory_available_gb"] = round(mem.available / (1024**3), 2)
            info["memory_percent"] = mem.percent
            disk = psutil.disk_usage("/")
            info["disk_total_gb"] = round(disk.total / (1024**3), 1)
            info["disk_free_gb"] = round(disk.free / (1024**3), 1)
        except ImportError:
            pass
        return info

    def run_command(self, command: str, timeout: int = 30) -> dict[str, Any]:
        """Run a shell command safely with dangerous command validation."""
        from noufex_ai.modules.security.validation import validate_command, validate_command_safe
        # First validate against dangerous patterns
        validate_command(command)
        # Then run safely without shell=True
        return validate_command_safe(command, timeout)

    # ── File Operations ────────────────────────────────────────────────

    def list_directory(self, path: str = ".") -> dict[str, Any]:
        """List contents of a directory with path validation."""
        try:
            from noufex_ai.modules.security.validation import validate_path
            p = validate_path(path, must_exist=True)
            if not p.is_dir():
                return {"success": False, "error": f"Path is not a directory: {path}"}
            items = []
            for child in p.iterdir():
                items.append({
                    "name": child.name,
                    "is_dir": child.is_dir(),
                    "size_bytes": child.stat().st_size if child.is_file() else 0,
                })
            return {
                "success": True,
                "path": str(p),
                "items": sorted(items, key=lambda x: (not x["is_dir"], x["name"])),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_file(self, path: str, max_size_kb: int = 100) -> dict[str, Any]:
        """Read a file's contents with path validation."""
        try:
            from noufex_ai.modules.security.validation import validate_path
            p = validate_path(path, must_exist=True, must_be_file=True)
            if p.stat().st_size > max_size_kb * 1024:
                return {"success": False, "error": f"File too large ({p.stat().st_size / 1024:.1f} KB)"}
            return {"success": True, "content": p.read_text(encoding="utf-8")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, path: str, content: str) -> dict[str, Any]:
        """Write content to a file with path validation."""
        try:
            from noufex_ai.modules.security.validation import validate_path
            p = validate_path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(p), "size_bytes": p.stat().st_size}
        except Exception as e:
            return {"success": False, "error": str(e)}
