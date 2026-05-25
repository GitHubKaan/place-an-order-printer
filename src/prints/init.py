from datetime import datetime

from src.utils.config import PrinterConfig, get_printer
from src.utils.format import FormatUtil

class InitPrint:
    @staticmethod
    def success() -> None:
        """
        Initial print when WebSocket connection is successfull
        """

        print("Printing initial success receipt.")

        try:
            printer = get_printer()
            printer.set(font="a")

            printer.set(align="center")
            checkmark_img = str(FormatUtil.checkmark_img())
            printer.image(checkmark_img)
            printer.text("\n\n")

            printer.set(align="center", bold=True, width=2, height=2)
            printer.text("System erfolgreich verbunden!\n\n")

            printer.set(align="left", bold=False, width=1, height=1)
            printer.text("System wurde erfolgreich mit den Place An Order\n")
            printer.text(f"Servern am {FormatUtil.current_date_time()} verbunden.\n")
            printer.text("Das Gerät ist nun einsatzbereit.\n")

            FormatUtil.line()

            footer_img = str(FormatUtil.footer_img())
            printer.image(footer_img)

            printer.cut()

            print("Initial success receipt successfully printed.")

        except Exception as exc:
            print(f"Error while printing: {exc}")
            raise

        finally:
            try:
                printer.close()
                PrinterConfig._printer_instance = None
            except Exception:
                pass

    @staticmethod
    def failure() -> None:
        """
        Initial print when WebSocket connection is NOT successfull
        """

        print("Printing initial failure receipt.")

        try:
            printer = get_printer()
            printer.set(font="a")

            printer.set(align="center")
            sad_face_img = str(FormatUtil.sad_face_img())
            printer.image(sad_face_img)
            printer.text("\n\n")

            printer.set(align="center", bold=True, width=2, height=2)
            printer.text("Verbindungsaufbau fehlgeschlagen!\n\n")

            printer.set(align="left", bold=False, width=1, height=1)
            printer.text("System konnte sich nicht mit den Place An Order\n")
            printer.text(f"Servern am {FormatUtil.current_date_time()} verbinden.\n")

            FormatUtil.line()

            footer_img = str(FormatUtil.footer_img())
            printer.image(footer_img)

            printer.cut()

            print("Initial failure receipt successfully printed.")

        except Exception as exc:
            print(f"Error while printing: {exc}")
            raise

        finally:
            try:
                printer.close()
                PrinterConfig._printer_instance = None
            except Exception:
                pass