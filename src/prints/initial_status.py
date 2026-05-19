from datetime import datetime
from pathlib import Path
from escpos.printer import Usb
from src.utils.config import printer

_RUNTIME_DIR = Path("/run/place-an-order-printer")


def _get_boot_marker_path() -> Path:
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    return _RUNTIME_DIR / f"boot-{boot_id}"


def _initial_status_already_printed() -> bool:
    try:
        return _get_boot_marker_path().exists()
    except Exception:
        return False  # Im Zweifel lieber nochmal drucken als crashen


def _mark_initial_status_printed() -> None:
    try:
        path = _get_boot_marker_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(datetime.now().isoformat())
    except Exception as e:
        print(f"Warning: Could not write boot marker: {e}")


def _do_print_receipt(status_line: str, console_msg: str) -> None:
    """Gemeinsame Drucklogik für success/failure."""
    if _initial_status_already_printed():
        print("Initial startup receipt already printed for this boot.")
        return

    try:
        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        printer.set(align="center", bold=True, width=2, height=2)
        printer.text("SYSTEM START\n")
        printer.set(align="center", bold=False, width=1, height=1)
        printer.text("==============================\n")
        printer.set(align="left")
        printer.text("Place An Order Printer\n")
        printer.text(f"Zeitpunkt: {now}\n")
        printer.text("\n")
        printer.text("==============================\n")
        printer.set(align="center", bold=True)
        printer.text(f"{status_line}\n")
        printer.text("\n\n")
        printer.cut()
        print(console_msg)
        _mark_initial_status_printed()
    except Exception as exc:
        print(f"Failed to print receipt: {exc}")
        raise

def print_initial_status() -> None:
    _do_print_receipt(
        status_line="System erfolgreich mit Place An Order Servern verbunden",
        console_msg="Initial startup receipt printed.",
    )


def print_initial_failure() -> None:
    _do_print_receipt(
        status_line="Systemstart konnte sich nicht mit Place An Order Servern verbinden",
        console_msg="Initial failure receipt printed.",
    )