import csv


def generate_csv(warehouse_payload: dict) -> str:
    """
    Generates a warehouse CSV from an already-transformed warehouse payload.
    """
    order_id = warehouse_payload["order_id"]
    csv_filename = f"order_{order_id}.csv"

    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Order ID",
            "Customer Name",
            "Address Line 1",
            "Address Line 2",
            "Address Line 3",
            "Unit",
            "Delivery Date",
            "SKU",
            "Quantity",
        ])

        for item in warehouse_payload["line_items"]:
            writer.writerow([
                warehouse_payload["order_id"],
                warehouse_payload["customer_name"],
                warehouse_payload["address_line_1"],
                warehouse_payload["address_line_2"],
                warehouse_payload["address_line_3"],
                warehouse_payload["unit"],
                warehouse_payload["delivery_date"],
                item["sku"],
                item["qty"],
            ])

    return csv_filename
