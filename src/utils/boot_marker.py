import platform
import subprocess
from pathlib import Path
from datetime import datetime

class BootMarkerUtil:
    _RUNTIME_DIR = Path("/run/place-an-order-printer")

    @staticmethod
    def _get_boot_id() -> str:
        if platform.system() == "Linux":
            return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        elif platform.system() == "Darwin":
            result = subprocess.run(
                ["sysctl", "-n", "kern.boottime"],
                capture_output=True, text=True, check=True
            )
            # Output: "{ sec = 1234567890, usec = 0 } ..."
            sec = result.stdout.split("sec =")[1].split(",")[0].strip()
            return f"mac-{sec}"
        return "dev-fallback"

    @staticmethod
    def _get_boot_marker_path() -> Path:
        if platform.system() == "Darwin":
            runtime_dir = Path("/tmp/place-an-order-printer")
        else:
            runtime_dir = BootMarkerUtil._RUNTIME_DIR
        boot_id = BootMarkerUtil._get_boot_id()
        return runtime_dir / f"boot-{boot_id}"

    @staticmethod
    def _initial_status_already_printed() -> bool:
        try:
            return BootMarkerUtil._get_boot_marker_path().exists()
        except Exception:
            return False

    @staticmethod
    def _mark_initial_status_printed() -> None:
        try:
            path = BootMarkerUtil._get_boot_marker_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(datetime.now().isoformat())
        except Exception as e:
            print(f"Warning: Could not write boot marker: {e}")

    @staticmethod
    def check_init_print() -> bool:
        path = BootMarkerUtil._get_boot_marker_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = path.open("x")
            fd.write(datetime.now().isoformat())
            fd.close()
            return True
        except FileExistsError:
            print("Initial startup receipt already printed for this boot.")
            return False
        except Exception as e:
            print(f"[ WARNING ] Boot marker check failed: {e}")
            return False