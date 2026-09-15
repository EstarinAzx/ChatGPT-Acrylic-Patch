"""Read-only check: python checks/chatgpt-acrylic.py (Windows desktop session)."""
import ctypes
import json
from ctypes import wintypes
from pathlib import Path

settings = Path.home() / "AppData/Local/Packages/DongleInsovaki.MicaForEveryone_t8299cmby5bjr/LocalState/settings.json"
rules = json.loads(settings.read_text(encoding="utf-8-sig"))["rules"]
matches = [rule for rule in rules if rule.get("type") == "process" and rule.get("processName") == "ChatGPT"]
assert len(matches) == 1 and matches[0]["backdropPreference"] == "Acrylic", "Expected one ChatGPT Acrylic rule"
assert matches[0]["enableBlurBehind"] is False, "Legacy Blur Behind must be off: it darkens maximized Owl windows"

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
kernel32 = ctypes.windll.kernel32
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
target = r"D:\Documents\ChatGPT-Acrylic\app\ChatGPT.exe"
windows = []


@ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
def inspect_window(hwnd, _):
    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(wintypes.HWND(hwnd), title, len(title))
    if title.value == "ChatGPT" and user32.IsWindowVisible(wintypes.HWND(hwnd)) and not user32.IsIconic(wintypes.HWND(hwnd)):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        process = kernel32.OpenProcess(0x1000, False, pid.value)
        if not process:
            return True
        try:
            path = ctypes.create_unicode_buffer(2048)
            size = wintypes.DWORD(len(path))
            if not kernel32.QueryFullProcessImageNameW(process, 0, path, ctypes.byref(size)) or path.value.casefold() != target.casefold():
                return True
        finally:
            kernel32.CloseHandle(process)
        material = ctypes.c_int()
        result = dwmapi.DwmGetWindowAttribute(wintypes.HWND(hwnd), 38, ctypes.byref(material), 4)
        windows.append((hwnd, material.value, result))
    return True


assert user32.EnumWindows(inspect_window, 0), "Could not enumerate desktop windows"
assert windows, "Open the editable ChatGPT test window (not minimized) before running this check"
assert all(material == 3 and result == 0 for _, material, result in windows), windows
print("PASS: legacy Blur Behind is off; the editable ChatGPT window reports native Acrylic (3).")
print("Visual confirmation is still needed: opaque chat surfaces can cover a native backdrop.")
