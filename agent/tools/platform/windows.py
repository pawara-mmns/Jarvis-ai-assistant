from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import winreg


@dataclass(frozen=True)
class ActiveWindow:
    app: str
    title: str


class WindowsDesktop:
    _folder_registry_names = {
        "desktop": "Desktop",
        "documents": "Personal",
        "pictures": "My Pictures",
        "downloads": "{374DE290-123F-4565-9164-39C4925E467B}",
        "videos": "My Video",
        "music": "My Music",
    }

    def launch_executable(self, executable: Path) -> None:
        subprocess.Popen(
            [str(executable)],
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )

    def open_shell_target(self, target: str) -> None:
        shell_execute = ctypes.windll.shell32.ShellExecuteW
        shell_execute.argtypes = (
            wintypes.HWND,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            ctypes.c_int,
        )
        shell_execute.restype = ctypes.c_void_p
        result = shell_execute(None, "open", target, None, None, 1)
        result_code = int(result or 0)
        if result_code <= 32:
            raise OSError(f"Windows could not open the requested target ({result_code})")

    def resolve_known_folder(self, alias: str) -> Path:
        value_name = self._folder_registry_names[alias]
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            ) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
            return Path(os.path.expandvars(value)).resolve()
        except OSError:
            fallback = "Documents" if alias == "documents" else alias.capitalize()
            return (Path.home() / fallback).resolve()

    def set_output_volume(self, level: int) -> None:
        import comtypes
        from pycaw.pycaw import AudioUtilities

        comtypes.CoInitialize()
        try:
            AudioUtilities.GetSpeakers().EndpointVolume.SetMasterVolumeLevelScalar(level / 100, None)
        finally:
            comtypes.CoUninitialize()

    def set_output_muted(self, muted: bool) -> None:
        import comtypes
        from pycaw.pycaw import AudioUtilities

        comtypes.CoInitialize()
        try:
            AudioUtilities.GetSpeakers().EndpointVolume.SetMute(1 if muted else 0, None)
        finally:
            comtypes.CoUninitialize()

    def get_active_window(self) -> ActiveWindow:
        user32 = ctypes.windll.user32
        get_foreground_window = user32.GetForegroundWindow
        get_foreground_window.restype = wintypes.HWND
        window = get_foreground_window()
        if not window:
            raise OSError("No foreground window")

        get_title_length = user32.GetWindowTextLengthW
        get_title_length.argtypes = (wintypes.HWND,)
        get_title_length.restype = ctypes.c_int
        get_title = user32.GetWindowTextW
        get_title.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
        get_title.restype = ctypes.c_int
        get_process_id = user32.GetWindowThreadProcessId
        get_process_id.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
        get_process_id.restype = wintypes.DWORD

        title_length = get_title_length(window)
        title_buffer = ctypes.create_unicode_buffer(title_length + 1)
        get_title(window, title_buffer, len(title_buffer))
        process_id = wintypes.DWORD()
        get_process_id(window, ctypes.byref(process_id))
        executable = self._process_name(process_id.value)
        return ActiveWindow(app=self._friendly_app_name(executable), title=title_buffer.value[:160])

    def capture_screenshot(self, destination: Path) -> None:
        from PIL import ImageGrab

        image = ImageGrab.grab(all_screens=True)
        image.save(destination, format="PNG")

    @staticmethod
    def _process_name(process_id: int) -> str:
        kernel32 = ctypes.windll.kernel32
        open_process = kernel32.OpenProcess
        open_process.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        open_process.restype = wintypes.HANDLE
        process = open_process(0x1000, False, process_id)
        if not process:
            return "Application"
        try:
            query_name = kernel32.QueryFullProcessImageNameW
            query_name.argtypes = (
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.LPWSTR,
                ctypes.POINTER(wintypes.DWORD),
            )
            query_name.restype = wintypes.BOOL
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not query_name(process, 0, buffer, ctypes.byref(size)):
                return "Application"
            return Path(buffer.value).stem
        finally:
            close_handle = kernel32.CloseHandle
            close_handle.argtypes = (wintypes.HANDLE,)
            close_handle.restype = wintypes.BOOL
            close_handle(process)

    @staticmethod
    def _friendly_app_name(executable: str) -> str:
        names = {
            "code": "Visual Studio Code",
            "chrome": "Google Chrome",
            "msedge": "Microsoft Edge",
            "explorer": "File Explorer",
            "notepad": "Notepad",
            "calculatorapp": "Calculator",
            "applicationframehost": "Windows application",
        }
        return names.get(executable.casefold(), executable or "Application")
