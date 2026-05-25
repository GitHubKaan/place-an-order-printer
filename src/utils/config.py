from escpos.printer import Usb
from src.utils.env_reader import EnvReaderUtil

class PrinterConfig:
    """
    Printer configuration for Epson TM-T20III
    """

    USB_VENDOR_ID = 0x04B8
    USB_PRODUCT_ID = 0x0E28
    USB_IN_EP = 0x82
    USB_OUT_EP = 0x01

    _printer_instance = None

    @classmethod
    def get_printer(cls) -> Usb:
        if cls._printer_instance is None:
            env = EnvReaderUtil.from_env()

            printer = Usb(
                cls.USB_VENDOR_ID,
                cls.USB_PRODUCT_ID,
                timeout=0,
                in_ep=cls.USB_IN_EP,
                out_ep=cls.USB_OUT_EP,
            )

            printer.profile.profile_data["media"]["width"]["pixel"] = env.printer_paper_pixel_width

            cls._printer_instance = printer

        return cls._printer_instance


def get_printer() -> Usb:
    """
    Shortcut to avoid writing PrinterConfig.get_printer() everywhere.
    """

    return PrinterConfig.get_printer()