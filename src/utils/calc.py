from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

def _safe_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        return Decimal("0.00")

class CalcUtil:
    @staticmethod
    def totals(order: dict) -> dict:
        tax_rate = Decimal("0.19")
        subtotal = Decimal("0.00")
        discount_total = Decimal("0.00")
        additional_discount = _safe_decimal(order.get("additionalDiscount", 0))
        items = []

        for product in order.get("orderedProducts", []) or []:
            unit_price = _safe_decimal(product.get("price", 0))
            discount = _safe_decimal(product.get("discount", 0))
            quantity = _safe_decimal(product.get("quantity", 0))
            extras = product.get("extraOptions") or []

            extras_total = Decimal("0.00")
            extra_lines = []
            for extra in extras:
                extra_price = _safe_decimal(extra.get("price", 0))
                extra_name = extra.get("name", "Zusatz")
                extra_lines.append({"name": extra_name, "price": extra_price})
                extras_total += extra_price

            item_base = unit_price + extras_total - discount
            item_total = item_base * quantity
            subtotal += item_total
            discount_total += discount * quantity

            items.append(
                {
                    "name": product.get("name", "Artikel"),
                    "description": product.get("description"),
                    "note": product.get("note"),
                    "quantity": int(quantity),
                    "unit_price": unit_price,
                    "extras": extra_lines,
                    "discount": discount,
                    "line_total": item_total,
                }
            )

        total_after_discounts = subtotal - additional_discount
        if total_after_discounts < Decimal("0.00"):
            total_after_discounts = Decimal("0.00")

        net_total = (total_after_discounts / (Decimal("1.00") + tax_rate)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        tax_total = total_after_discounts - net_total

        return {
            "items": items,
            "subtotal": subtotal,
            "discount_total": discount_total,
            "additional_discount": additional_discount,
            "net_total": net_total,
            "tax_total": tax_total,
            "gross_total": total_after_discounts,
            "tax_rate": tax_rate,
        }