from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

def _safe_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        return Decimal("0.00")

class CalcUtil:
    @staticmethod
    def totals(order: dict) -> dict:
        additional_discount = _safe_decimal(order.get("additionalDiscount", 0))
        items = []
        rate_gross: dict[str, Decimal] = defaultdict(Decimal)

        for product in order.get("orderedProducts", []) or []:
            unit_price = _safe_decimal(product.get("price", 0))
            discount = _safe_decimal(product.get("discount", 0))
            quantity = _safe_decimal(product.get("quantity", 0))
            # taxRate from API is a percentage (e.g. 19.00 for 19%). Fall back to 19 if absent.
            tax_rate = _safe_decimal(product.get("taxRate") or 19)
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

            rate_key = str(tax_rate.normalize())
            rate_gross[rate_key] += item_total

            items.append({
                "name": product.get("name", "Artikel"),
                "description": product.get("description"),
                "note": product.get("note"),
                "quantity": int(quantity),
                "unit_price": unit_price,
                "extras": extra_lines,
                "discount": discount,
                "line_total": item_total,
                "tax_rate": tax_rate,
            })

        subtotal = sum(rate_gross.values())

        # Sort rates descending (19% → A, 7% → B, …) for German-standard labeling
        sorted_rates = sorted(rate_gross.keys(), key=lambda r: Decimal(r), reverse=True)
        label_map = {rate_key: chr(ord("A") + i) for i, rate_key in enumerate(sorted_rates)}

        # Distribute additional_discount proportionally across tax groups.
        # Last group absorbs any rounding remainder to keep grand total exact.
        tax_groups: dict[str, dict] = {}
        distributed = Decimal("0.00")

        for idx, rate_key in enumerate(sorted_rates):
            group_gross_before = rate_gross[rate_key]
            rate = Decimal(rate_key)

            if subtotal > Decimal("0") and additional_discount > Decimal("0"):
                if idx < len(sorted_rates) - 1:
                    share = (group_gross_before / subtotal * additional_discount).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                else:
                    share = additional_discount - distributed
                distributed += share
            else:
                share = Decimal("0.00")

            group_gross = max(group_gross_before - share, Decimal("0.00"))

            # Extract net and tax from gross (tax-inclusive prices, §ermann § 14 UStG)
            divisor = Decimal("1") + rate / Decimal("100")
            if divisor == Decimal("1"):
                group_net = group_gross
                group_tax = Decimal("0.00")
            else:
                group_net = (group_gross / divisor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                group_tax = group_gross - group_net

            tax_groups[rate_key] = {
                "label": label_map[rate_key],
                "rate": rate,
                "gross": group_gross,
                "net": group_net,
                "tax": group_tax,
            }

        for item in items:
            rate_key = str(item["tax_rate"].normalize())
            item["tax_label"] = label_map.get(rate_key, "")

        return {
            "items": items,
            "subtotal": subtotal,
            "additional_discount": additional_discount,
            "net_total": sum(g["net"] for g in tax_groups.values()),
            "tax_total": sum(g["tax"] for g in tax_groups.values()),
            "gross_total": sum(g["gross"] for g in tax_groups.values()),
            "tax_groups": tax_groups,
        }
