"""Windows integration helpers for Genenote."""

import ctypes
import os
import sys
import winreg
from importlib import resources
from pathlib import Path

from genenote import projectio


LAUNCHER_FILENAME = "base.genenote"
FILE_CLASS_NAME = "GenenoteFile"
FILE_CLASS_LABEL = "Genenote File"
FOLDER_MENU_KEY = r"Software\Classes\Directory\shell\GenenoteBase"
APP_USER_MODEL_ID = "LionKimbro.Genenote"


def intercept_genenote_launcher_invocation():
    """Handle Explorer launcher-file invocation before lionscliapp parses argv."""

    if len(sys.argv) != 2:
        return False

    arg_path = Path(sys.argv[1]).expanduser().resolve()
    if not arg_path.is_file():
        return False

    if arg_path.name.lower() != LAUNCHER_FILENAME.lower():
        return False

    os.chdir(arg_path.parent)
    sys.argv[:] = [sys.argv[0]]
    return True


def rewrite_base_command_argv():
    """Rewrite 'genenote base <folder>' into lionscliapp-compatible argv."""

    if len(sys.argv) != 3:
        return False

    if sys.argv[1] != "base":
        return False

    target = str(Path(sys.argv[2]).expanduser().resolve())
    sys.argv[:] = [sys.argv[0], "--path.target_folder", target, "base"]
    return True


def maybe_handle_direct_command():
    """Handle commands that should run before lionscliapp startup."""

    if len(sys.argv) == 2 and sys.argv[1] == "install":
        command_install()
        print("Installed Genenote Windows integration.")
        return True

    if len(sys.argv) in (2, 3) and sys.argv[1] == "base":
        target = Path.cwd() if len(sys.argv) == 2 else Path(sys.argv[2]).expanduser().resolve()
        launcher_path = command_base(target)
        print(f"Created {launcher_path}")
        return True

    return False


def get_icon_path():
    """Return an absolute filesystem path to the Genenote icon."""

    candidates = []

    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable))
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "genenote" / "assets" / "icon" / "favicon.ico")
            candidates.append(Path(meipass) / "assets" / "icon" / "favicon.ico")

    try:
        package_file = resources.files("genenote").joinpath("assets/icon/favicon.ico")
        if package_file.is_file():
            try:
                candidates.append(Path(package_file))
            except TypeError:
                pass
    except Exception:
        pass

    module_root = Path(__file__).resolve().parents[2]
    candidates.append(module_root / "assets" / "icon" / "favicon.ico")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())

    raise FileNotFoundError("Could not locate Genenote icon resource")


def set_windows_appusermodel_id():
    """Set the Windows AppUserModelID for taskbar grouping."""

    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        return


def set_windows_tk_icon(window):
    """Set the Tk icon on Windows if possible."""

    if sys.platform != "win32":
        return

    try:
        window.iconbitmap(get_icon_path())
    except Exception:
        return


def command_base(target_folder):
    """Create a Genenote launcher file and ensure project structure."""

    target_dir = Path(target_folder).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(target_dir)

    projectio.ensure_project_structure(target_dir / ".genenote")

    launcher_path = target_dir / LAUNCHER_FILENAME
    if not launcher_path.exists():
        launcher_path.write_text("Genenote launcher file\n", encoding="utf-8")

    return launcher_path


def command_install():
    """Install Windows shell integration in HKCU\\Software\\Classes."""

    if sys.platform != "win32":
        raise RuntimeError("genenote install is only supported on Windows")

    icon_path = get_icon_path()
    open_command = build_open_command("%1")
    base_command = build_base_command("%1")

    _write_classes_default(r"Software\Classes\.genenote", FILE_CLASS_NAME)
    _write_classes_default(rf"Software\Classes\{FILE_CLASS_NAME}", FILE_CLASS_LABEL)
    _write_classes_default(rf"Software\Classes\{FILE_CLASS_NAME}\DefaultIcon", icon_path)
    _write_classes_default(
        rf"Software\Classes\{FILE_CLASS_NAME}\shell\open\command",
        open_command,
    )

    _write_classes_default(FOLDER_MENU_KEY, "Add Genenote Instance")
    _write_classes_default(FOLDER_MENU_KEY + r"\command", base_command)

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.genenote\ShellNew") as key:
        winreg.SetValueEx(key, "NullFile", 0, winreg.REG_SZ, "")

    _notify_shell_of_changes()


def build_open_command(target_placeholder):
    """Return the file association command string."""

    executable, launcher = _resolve_command_launcher()
    if launcher is None:
        return f'"{executable}" "{target_placeholder}"'
    return f'"{executable}" {launcher} "{target_placeholder}"'


def build_base_command(target_placeholder):
    """Return the Explorer folder context-menu command string."""

    executable, launcher = _resolve_command_launcher()
    if launcher is None:
        return f'"{executable}" base "{target_placeholder}"'
    return f'"{executable}" {launcher} base "{target_placeholder}"'


def _resolve_command_launcher():
    """Resolve how Windows should invoke Genenote."""

    if getattr(sys, "frozen", False):
        return sys.executable, None

    return sys.executable, "-m genenote"


def _write_classes_default(subkey_path, value):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey_path) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, value)


def _notify_shell_of_changes():
    """Ask Explorer to refresh file associations."""

    try:
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
    except Exception:
        return
