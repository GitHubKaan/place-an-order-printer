from pathlib import Path
from escpos.printer import Usb
from PIL import Image

from src.utils.config import PrinterConfig, get_printer
from src.utils.calc import CalcUtil
from src.utils.format import FormatUtil
from src.utils.env_reader import EnvReaderUtil

class ReceiptPrint:
    @staticmethod
    def _extract_data(data: dict) -> dict:
        if isinstance(data.get("data"), dict):
            return data["data"]
        return data

    @staticmethod
    def receipt(data: dict) -> None:
        """
        Print a receipt from the provided API response data
        """

        print("Printing receipt.")

        data = ReceiptPrint._extract_data(data)
        totals = CalcUtil.totals(data.get("order"))

        try:
            # ===== Initial settings =============================================================================================
            printer = get_printer()
            printer.set(font="a")

            # ===== Receipt top =============================================================================================
            printer.set(align="center")
            printer.text(f"{data.get("user").get("company")}\n")
            printer.text(f"{data.get("user").get("street")} {data.get("user").get("streetNumber")}\n")
            printer.text(f"{data.get("user").get("ZIPCode")} {data.get("user").get("city")}\n")
            printer.text(f"{data.get("user").get("country")}\n")
            printer.text("\n")

            # ===== Warning messages =============================================================================================
            printer.set(align="center", bold=True, width=2, height=2)
            canceled = data.get("order").get("canceled")
            if canceled:
                printer.text("+++ BESTELLUNG WURDE STORNIERT +++\n")

            paid = data.get("order").get("paid")
            if not paid:
                printer.text("+++ BESTELLUNG WURDE NICHT BEZAHLT +++\n")

            printer.text("\n")

            # ===== General info =============================================================================================
            printer.set(align="left", bold=True, width=2, height=2)
            printer.text("Kassenbeleg\n\n")

            printer.set(align="left", bold=False, width=1, height=1)
            receipt_id = data.get("id")
            receipt_id_left_right = FormatUtil.left_right("Beleg-ID:", receipt_id)
            printer.text(receipt_id_left_right)

            order_uuid = data.get("order").get("UUID")
            order_uuid_left_right = FormatUtil.left_right("Bestell-ID:", order_uuid)
            printer.text(order_uuid_left_right)

            printer.text("\n")

            current_date = data.get("updated")
            current_date_timestamp = FormatUtil.format_timestamp(current_date)
            current_date_left_right = FormatUtil.left_right("Datum:", current_date_timestamp)
            printer.text(current_date_left_right)

            receipt_date = data.get("created")
            receipt_date_timestamp = FormatUtil.format_timestamp(receipt_date)
            receipt_date_left_right = FormatUtil.left_right("Belegdatum:", receipt_date_timestamp)
            printer.text(receipt_date_left_right)

            order_date = data.get("order").get("created")
            order_date_timestamp = FormatUtil.format_timestamp(order_date)
            order_date_left_right = FormatUtil.left_right("Bestelldatum:", order_date_timestamp)
            printer.text(order_date_left_right)

            printer.text("\n")

            table_number = data.get("order").get("tableNumber")
            if table_number is not None:
                table_number_left_right = FormatUtil.left_right("Tischnummer:", str(table_number))
                printer.text(table_number_left_right)
            else:
                to_go_name = data.get("order").get("toGoName")
                to_go_name_left_right = FormatUtil.left_right("To-go-Name:", to_go_name)
                printer.text(to_go_name_left_right)

            FormatUtil.line()

            # ===== Ordered items =============================================================================================
            for item in totals["items"]:
                item_left_right = FormatUtil.left_right(f"{item['quantity']}x {item['name']}", f"{FormatUtil.format_money(item['unit_price'])}    {FormatUtil.format_money(item['line_total'])}")
                printer.text(item_left_right)

                if item["discount"] > 0:
                    printer.text(f"    Rabatt: -{FormatUtil.format_money(item['discount'])}\n")
                
                for extra in item["extras"]:
                    printer.text(f"    + {extra['name']} ({FormatUtil.format_money(extra['price'])})\n")
                
                if item["note"]:
                    printer.text(f"    Hinweis: {item['note']}\n")

            FormatUtil.line()

            # ===== Calculation =============================================================================================
            subtotal_left_right = FormatUtil.left_right("Zwischensumme:", f"{FormatUtil.format_money(totals['subtotal'])}")
            printer.text(subtotal_left_right)

            if totals["additional_discount"] > 0:
                total_discount_left_right = FormatUtil.left_right("Zusätzlicher Rabatt:", f"-{FormatUtil.format_money(totals['additional_discount'])}")
                printer.text(total_discount_left_right)

            netto_left_right = FormatUtil.left_right("Netto:", f"{FormatUtil.format_money(totals['net_total'])}")
            printer.text(netto_left_right)

            netto_left_right = FormatUtil.left_right(f"MwSt. ({int(totals['tax_rate'] * 100)}%):", f"{FormatUtil.format_money(totals['tax_total'])}")
            printer.text(netto_left_right)

            total_left_right = FormatUtil.left_right("Gesamtbetrag:", f"{FormatUtil.format_money(totals['gross_total'])}")
            printer.text(total_left_right)

            FormatUtil.line()

            # ===== Footer =============================================================================================
            footer_img = str(FormatUtil.footer_img())
            printer.image(footer_img)
            
            printer.cut()

            print("Receipt printed successfully: %s", receipt_id)

        except Exception as exc:
            print("Error while printing: %s", exc)
            raise

        finally:
            try:
                printer.close()
            except Exception:
                pass