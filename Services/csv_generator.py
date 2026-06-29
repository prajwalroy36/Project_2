import csv
from datetime import datetime,timedelta
from Schemas.Order import  OrderPayload

def clean_and_transform_data(raw_payload: dict)-> str: 
    payload = OrderPayload.model_validate(raw_payload)
    order_id = payload.order_id

    #RULE 1 ~ SLICING STRING LIMIT TO MAXIMUM '30' CHARACTERS

    raw_address = payload.customer.address
    truncated_address = raw_address[:30]

    #RULE 2 ~ CALCAULATE OPERATIONAL 10AM CUTOFF DATE PARAMETERS

    order_time = datetime.strptime(payload.timestamp,"%Y-%m-%dT%H:%M:%SZ") # why did d light up?,where does "timestamp" come from?
    if order_time.hour >= 10:
        delivery_date = order_time + timedelta(days=1) #timedelta datetime module
    else:
        delivery_date = order_time
    
    #skip weekend safely
    if delivery_date.weekday()== 5: delivery_date += timedelta(days=2)
    elif delivery_date.weekday()== 6: delivery_date += timedelta(days=1)
    formatted_date = delivery_date.strftime("%m/%d/%Y")

    # ~GENERATE CSV LINE STRUCTURE~

    csv_filename = f"order_{order_id}.csv"
    with open (csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Order Id", "Customer Name", "Truncated Address", "Unit", "Delivery Date","SKU", "Quantity"])
        for item in payload.line_items:
            writer.writerow([order_id, payload.customer.name, truncated_address, "Each",formatted_date,item.sku,item.qty])
    return csv_filename