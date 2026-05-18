from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from escpos.printer import Usb
from PIL import Image

from src.utils.config import printer
from src.utils.calc import calculate_totals

def _prepare_logo() -> Path | None:
    """
    Convert the source logo to a 1-bit image compatible with the printer.
    Returns the processed image path or None if the source image is missing.
    """

    logo_src = Path("assets") / "logo" / "pao_logo_black_v1.png"
    logo_dest = Path("assets") / "logo" / "pao_logo_resized.png"

    if not logo_src.exists():
        print("Logo not found at '%s' - skipping logo.", logo_src)
        return None

    img = Image.open(logo_src).convert("RGBA")

    # Apply white background behind transparent areas
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    background.paste(img, mask=img.split()[3])

    img = background.convert("RGB")

    # Resize while preserving aspect ratio
    logo_width = 400
    height = int(img.height * (logo_width / img.width))
    img = img.resize((logo_width, height), Image.LANCZOS)

    # Convert image to black and white
    img = img.convert("1")

    logo_dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(logo_dest)

    print("Logo prepared: %s", logo_dest)

    return logo_dest


def _format_timestamp(timestamp: str) -> str:
    """
    Convert ISO timestamp into a readable date format.
    """

    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%d.%m.%Y  %H:%M:%S")
    except (ValueError, TypeError):
        return str(timestamp)

def _format_money(value: Decimal) -> str:
    amount = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:.2f} €"

def _extract_order_data(data: dict) -> dict:
    if isinstance(data.get("order"), dict):
        return data["order"]
    return data

def print_receipt(data: dict) -> None:
    """
    Print a receipt from the provided API response data.

    Supports both the current API payload and the raw order structure.
    """

    order_data = _extract_order_data(data)

    receipt_id = data.get("id") or order_data.get("UUID") or order_data.get("uuid") or "–"
    created_raw = data.get("created") or order_data.get("created") or "–"
    created = _format_timestamp(created_raw)
    order_uuid = order_data.get("UUID") or order_data.get("uuid") or "–"
    order_created = _format_timestamp(order_data.get("created") or created_raw)

    table_number = order_data.get("tableNumber")
    togo_id = order_data.get("toGoID")
    paid = order_data.get("paid")
    awaiting_payment = order_data.get("awaitingPayment")
    canceled = order_data.get("canceled")
    prepared = order_data.get("prepared")
    done = order_data.get("done")

    totals = calculate_totals(order_data)

    print("Printing receipt: %s", receipt_id)

    logo_path = _prepare_logo()

    try:
        if logo_path:
            printer.set(align="center")
            printer.image(str(logo_path))

        printer.set(align="center", bold=True, height=2, width=2)
        printer.text("Kundenbeleg\n")
        printer.set(align="center", bold=False, height=1, width=1)
        printer.text("==============================\n")

        printer.set(align="left", bold=False, height=1, width=1)
        printer.text("Place An Order\n")
        printer.text("Musterstraße 1\n")
        printer.text("12345 Musterstadt\n")
        printer.text("Deutschland\n")
        printer.text("Steuernummer: DE123456789\n")
        printer.text("USt-ID: DE123456789\n")
        printer.text("\n")

        printer.text(f"Belegnummer: {receipt_id}\n")
        printer.text(f"Belegdatum: {created}\n")
        printer.text(f"Auftrags-ID: {order_uuid}\n")
        printer.text(f"Auftragsdatum: {order_created}\n")
        if table_number is not None:
            printer.text(f"Tischnummer: {table_number}\n")
        if togo_id is not None:
            printer.text(f"To-Go ID: {togo_id}\n")
        printer.text(f"Status: {'Storniert' if canceled else 'Bezahlt' if paid else 'Unbezahlt'}\n")
        if awaiting_payment:
            printer.text("Zahlung: ausstehend\n")
        if prepared:
            printer.text("Zubereitet: ja\n")
        if done:
            printer.text("Ausgabe: abgeschlossen\n")

        printer.text("==============================\n")

        if totals["items"]:
            for item in totals["items"]:
                printer.text(f"{item['name']}\n")
                printer.text(
                    f"  {item['quantity']} x {_format_money(item['unit_price'])} = {_format_money(item['line_total'])}\n"
                )
                for extra in item["extras"]:
                    printer.text(f"    + {extra['name']}: {_format_money(extra['price'])}\n")
                if item["discount"] > 0:
                    printer.text(f"    Rabatt: -{_format_money(item['discount'] * item['quantity'])}\n")
                if item["description"]:
                    printer.text(f"    {item['description']}\n")
                if item["note"]:
                    printer.text(f"    Hinweis: {item['note']}\n")
                printer.text("\n")
        else:
            printer.text("Keine Artikel vorhanden.\n")

        printer.text("==============================\n")
        printer.text(f"Zwischensumme: {_format_money(totals['subtotal'])}\n")
        if totals["additional_discount"] > 0:
            printer.text(f"Gesamt-Rabatt: -{_format_money(totals['additional_discount'])}\n")
        printer.text(f"Netto: {_format_money(totals['net_total'])}\n")
        printer.text(f"MwSt. ({int(totals['tax_rate'] * 100)}%): {_format_money(totals['tax_total'])}\n")
        printer.text(f"Gesamtbetrag: {_format_money(totals['gross_total'])}\n")
        printer.text("Alle Preise inkl. MwSt.\n")
        printer.text("==============================\n")

        printer.set(align="center")
        printer.text("Vielen Dank für Ihren Einkauf!\n")
        printer.text("\n")
        printer.text("Dieser Beleg ist kein Steuerbeleg im Sinne einer Rechnung.\n")
        printer.text("Bitte bewahren Sie diesen Beleg auf.\n")
        printer.text("\n")

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