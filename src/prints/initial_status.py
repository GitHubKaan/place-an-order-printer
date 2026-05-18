from datetime import datetime
from pathlib import Path
from escpos.printer import Usb
from src.utils.config import printer

def _get_boot_marker_path() -> Path:
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    return Path(f"/run/place-an-order-printer/boot-{boot_id}")

def _initial_status_already_printed() -> bool:
    return _get_boot_marker_path().exists()

def _mark_initial_status_printed() -> None:
    try:
        path = _get_boot_marker_path()
        path.parent.mkdir(parents=True, exist_ok=True)  # ← Das fehlt!
        path.write_text(datetime.now().isoformat())
    except Exception as e:
        print(f"Warning: Could not write boot marker: {e}")

def print_initial_status() -> None:
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
        printer.text("System erfolgreich mit Place An Order Servern verbunden\n")
        printer.text("\n\n")
        printer.cut()
        print("Initial startup receipt printed.")
        _mark_initial_status_printed()
    except Exception as exc:
        print(f"Failed to print startup receipt: {exc}")
        raise
    finally:
        try:
            printer.close()
        except Exception:
            pass

def print_initial_failure() -> None:
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
        printer.text("Systemstart konnte sich nicht mit Place An Order Servern verbinden\n")
        printer.text("\n\n")
        printer.cut()
        print("Initial failure receipt printed.")
        _mark_initial_status_printed()
    except Exception as exc:
        print(f"Failed to print failure receipt: {exc}")
        raise
    finally:
        try:
            printer.close()
        except Exception:
            pass