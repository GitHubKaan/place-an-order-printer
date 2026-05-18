from datetime import datetime
from pathlib import Path
from escpos.printer import Usb

from src.utils.config import printer

BOOT_MARKER = Path("/run/place-an-order-printer-initial-status-printed")


def _initial_status_already_printed() -> bool:
    return BOOT_MARKER.exists()


def _mark_initial_status_printed() -> None:
    try:
        BOOT_MARKER.write_text(datetime.now().isoformat())
    except Exception:
        pass


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
        printer.text("System erfolgreich gestartet\n")

        printer.text("\n\n")

        printer.cut()

        print("Initial startup receipt printed.")
        _mark_initial_status_printed()

    except Exception as exc:
        print("Failed to print startup receipt: %s", exc)
        raise

    finally:
        try:
            printer.close()
        except Exception:
            pass