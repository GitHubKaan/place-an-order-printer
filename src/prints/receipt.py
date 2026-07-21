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

            # ===== To-go name (very top, bold, large, no wrap) =============================================================================================
            to_go_name = data.get("order").get("toGoName")
            if to_go_name is not None:
                printer.set(align="center", width=1, height=1, bold=False)
                printer.text("Deine ID lautet:\n")
                printer.image(FormatUtil.to_go_name_img(to_go_name))
                printer.text("\n")

            # ===== Receipt top =============================================================================================
            printer.set(align="center", bold=False, width=1, height=1)
            printer.text(f"{data.get("user").get("company")}\n")
            printer.text(f"{data.get("user").get("street")} {data.get("user").get("streetNumber")}\n")
            printer.text(f"{data.get("user").get("ZIPCode")} {data.get("user").get("city")}\n")
            printer.text(f"{data.get("user").get("country")}\n")
            vat_id = data.get("user").get("vatID")
            if vat_id:
                printer.text(f"USt-IdNr.: {vat_id}\n")
            tax_number = data.get("user").get("taxNumber")
            if tax_number:
                printer.text(f"Steuernr.: {tax_number}\n")
            printer.text("\n")

            # ===== Warning messages =============================================================================================
            printer.set(align="center", bold=True, width=2, height=2)
            canceled = data.get("order").get("canceled")
            if canceled:
                printer.text("+++ BESTELLUNG WURDE STORNIERT +++\n")

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

            printer.text("\n")

            paid = data.get("order").get("paid")
            if paid:
                paid_left_right = FormatUtil.left_right("Bezahlstatus:", "BEZAHLT")
                printer.text(paid_left_right)
            else:
                paid_left_right = FormatUtil.left_right("Bezahlstatus:", "OFFEN")
                printer.text(paid_left_right)

            # Prefer the snapshot persisted on the receipt; fall back to deriving from the order
            # so receipts created before payment_method was persisted still print sensibly.
            payment_method = data.get("paymentMethod")
            if payment_method is None:
                stripe_used = (
                    data.get("order").get("stripeID") is not None
                    or data.get("order").get("stripePaymentIntent") is not None
                )
                payment_method = "CARD" if stripe_used else "CASH"

            payment_label = "KARTE" if payment_method == "CARD" else "BAR"
            printer.text(FormatUtil.left_right("Bezahlart:", payment_label))

            FormatUtil.line()

            # ===== Ordered items =============================================================================================
            multi_rate = len(totals["tax_groups"]) > 1
            for item in totals["items"]:
                label_suffix = f" [{item['tax_label']}]" if multi_rate else ""
                item_left_right = FormatUtil.left_right(f"{item['quantity']}x {item['name']}{label_suffix}", f"{FormatUtil.format_money(item['unit_price'])}    {FormatUtil.format_money(item['line_total'])}")
                printer.text(item_left_right)

                if item["discount"] > 0:
                    printer.text(f"    Rabatt: -{FormatUtil.format_money(item['discount'])}\n")

                for extra in item["extras"]:
                    printer.text(f"    + {extra['name']} ({FormatUtil.format_money(extra['price'])})\n")

                if item["note"]:
                    printer.text(f"    Hinweis: {item['note']}\n")

            FormatUtil.line()

            # ===== Calculation (§ 14 UStG: tax breakdown per rate group) =============================================================================================
            printer.text(FormatUtil.left_right("Zwischensumme:", FormatUtil.format_money(totals["subtotal"])))

            if totals["additional_discount"] > 0:
                printer.text(FormatUtil.left_right("Zusätzlicher Rabatt:", f"-{FormatUtil.format_money(totals['additional_discount'])}"))

            if multi_rate:
                # Compact tax table — § 14 UStG: Netto + MwSt. per rate is sufficient
                printer.text("Steuerausweis:\n")
                printer.text(f"{'':6}  {'Netto':>9}  {'MwSt.':>8}\n")
                for group in totals["tax_groups"].values():
                    label_col = f"{group['label']} {int(group['rate']):>3}%"
                    net_str = FormatUtil.format_money(group["net"])
                    tax_str = FormatUtil.format_money(group["tax"])
                    printer.text(f"{label_col}  {net_str:>9}  {tax_str:>8}\n")
            else:
                single = next(iter(totals["tax_groups"].values()))
                rate_pct = int(single["rate"])
                printer.text(FormatUtil.left_right("Netto:", FormatUtil.format_money(totals["net_total"])))
                printer.text(FormatUtil.left_right(f"MwSt. ({rate_pct}%):", FormatUtil.format_money(totals["tax_total"])))

            printer.text(FormatUtil.left_right("Gesamtbetrag:", FormatUtil.format_money(totals["gross_total"])))

            # ===== Cash given / change (GoBD: reconstruction of Wechselgeld) =============================================================================================
            given_amount = data.get("givenAmount")
            if payment_method == "CASH" and given_amount is not None:
                printer.text(FormatUtil.left_right("Gegeben:", FormatUtil.format_money(given_amount)))
                change = given_amount - totals["gross_total"]
                printer.text(FormatUtil.left_right("Rückgeld:", FormatUtil.format_money(max(change, 0))))
            
            # ===== TSE-Sicherheitsnachweis (KassenSichV §6) =============================================================================================
            # Text-only variant: alle §6-pflichtigen Werte werden lesbar gedruckt
            # (Vorgangsbeginn, Vorgangsende, Vorgangsart, Transaktionsnr., Seriennr. der TSE,
            #  Prüfwert + zur Auditor-Verifikation: Signaturalgorithmus, LogTimeFormat).
            # Vorgangsart wird durch den Belegtitel ("Kassenbeleg"/"Storno") abgedeckt.
            tse = data.get("tse")
            if tse and not tse.get("error"):
                printer.set(align="left", bold=False, width=1, height=1)
                FormatUtil.line()
                printer.set(align="center", bold=True, width=1, height=1)
                printer.text("TSE-Sicherheitsnachweis\n")
                printer.set(align="left", bold=False, width=1, height=1)

                tx_number = tse.get("txNumber")
                if tx_number is not None:
                    printer.text(FormatUtil.left_right("TSE-Tx-Nr.:", str(tx_number)))

                sig_counter = tse.get("signatureCounter")
                if sig_counter is not None:
                    printer.text(FormatUtil.left_right("Sig.-Zähler:", str(sig_counter)))

                serial = tse.get("serialNumber")
                if serial:
                    compact = f"{serial[:8]}...{serial[-7:]}" if len(serial) > 20 else serial
                    printer.text(FormatUtil.left_right("TSE-Seriennr.:", compact))

                tx_start = tse.get("txStart")
                if tx_start:
                    try:
                        printer.text(FormatUtil.left_right("Tx-Start:", FormatUtil.format_timestamp(tx_start)))
                    except Exception:
                        printer.text(FormatUtil.left_right("Tx-Start:", str(tx_start)))

                tx_end = tse.get("txEnd")
                if tx_end:
                    try:
                        printer.text(FormatUtil.left_right("Tx-Ende:", FormatUtil.format_timestamp(tx_end)))
                    except Exception:
                        printer.text(FormatUtil.left_right("Tx-Ende:", str(tx_end)))

                algorithm = tse.get("algorithm")
                if algorithm:
                    printer.text(FormatUtil.left_right("Algorithmus:", str(algorithm)))

                log_format = tse.get("logTimeFormat") or "unixTime"
                printer.text(FormatUtil.left_right("Log-Format:", str(log_format)))

                # Prüfwert (Signatur) — § 6 KassenSichV verlangt den vollständigen Wert
                # auf dem Beleg. Wird in einer Zeile gedruckt; der Drucker bricht selbst um.
                signature = tse.get("signature")
                if signature:
                    printer.text(f"Signatur: {signature}\n")

                # DSFinV-K Annex E QR-Code — vom Finanzamt mit der "Kassen-App"
                # (BMF/fiskalcheck) scannbar. Enthält alle §6-pflichtigen Werte in der
                # vom BSI vorgeschriebenen Reihenfolge.
                qr_payload = tse.get("qrPayload")
                if qr_payload:
                    printer.set(align="center", bold=False, width=1, height=1)
                    printer.text("\nTSE-QR (fiskalcheck):\n")
                    printer.qr(qr_payload, size=5)

                FormatUtil.line()

            elif tse and tse.get("error"):
                printer.set(align="left", bold=False, width=1, height=1)
                FormatUtil.line()
                printer.set(align="center", bold=True, width=1, height=1)
                printer.text("*** TSE NICHT VERFUEGBAR ***\n")
                printer.set(align="center", bold=False, width=1, height=1)
                printer.text("Beleg ohne TSE-Sicherung\n")
                FormatUtil.line()

            # ===== Digital receipt QR code =============================================================================================
            digital_url = data.get("digitalReceiptUrl")
            if digital_url:
                printer.set(align="center", bold=False, width=1, height=1)
                printer.text("Digitaler Beleg:")
                printer.qr(digital_url, size=4)
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