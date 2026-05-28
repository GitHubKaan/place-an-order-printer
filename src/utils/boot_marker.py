from pathlib import Path
from datetime import datetime


class BootMarkerUtil:
    _RUNTIME_DIR = Path("/run/place-an-order-printer")

    @staticmethod
    def _get_boot_marker_path() -> Path:
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        return BootMarkerUtil._RUNTIME_DIR / f"boot-{boot_id}"

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
        """Returns True if this is the first print this boot."""
        if BootMarkerUtil._initial_status_already_printed():
            print("Initial startup receipt already printed for this boot.")
            return False
        BootMarkerUtil._mark_initial_status_printed()
        return True