from pathlib import Path
from escpos.printer import Usb

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Startup status file written by the initial listener handshake.
STARTUP_FILE = PROJECT_ROOT / "var" / "startup_status.txt"

# USB printer configuration for Epson TM-T20III.
USB_VENDOR_ID = 0x04B8
USB_PRODUCT_ID = 0x0E28
USB_IN_EP = 0x82
USB_OUT_EP = 0x01

# Logo settings for receipt printing.
LOGO_SRC = PROJECT_ROOT / "assets" / "logo" / "pao_logo_black_v1.png"
LOGO_DEST = PROJECT_ROOT / "assets" / "logo" / "pao_logo_resized.png"
LOGO_WIDTH = 400

printer = Usb(
    USB_VENDOR_ID,
    USB_PRODUCT_ID,
    timeout=0,
    in_ep=USB_IN_EP,
    out_ep=USB_OUT_EP,
)