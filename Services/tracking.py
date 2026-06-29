import paramiko
import csv
import os
from Core.config import settings

def download_tracking_files():
    sftp = None
    transport = None

    downloaded_files = []

    try: 
        transport = paramiko.Transport((settings.SFTP_HOST, settings.SFTP_PORT))
        transport.connect(username=settings.SFTP_USER, password=settings.SFTP_PASS,)
        sftp = paramiko.SFTPClient.from_transport(transport)
        #look inside warehouse outgoing tracker folder
        tracking_dir = ""
        files = sftp.listdir(tracking_dir)

        for filename in files:
            if filename.endswith(".csv"):
                local_path = f"tracking_{filename}"
                remote_path = tracking_dir + filename
                sftp.get(tracking_dir + filename, local_path)
                downloaded_files.append({
                    "local_path": local_path,
                    "remote_path": remote_path
                })
                print(f"Tracking! download {filename} from warehouse")
        return downloaded_files
    finally:
        if sftp is not None:
            sftp.close()
        if transport is not None:
            transport.close()
    
def parse_tracking_file(local_path : str):

    tracking_records = []

    with open(local_path, mode= 'r') as file:

        reader = csv.reader(file)

        next(reader, None)

        for row in reader:
            if len(row) < 3:
                continue
            tracking_record = {
                "order_id": row[0],
                "tracking_number": row[1],
                "carrier": row[2]
    }

            tracking_records.append(tracking_record)
    
    return tracking_records

def update_order_tracking(tracking_records):
    for record in tracking_records:
        order_id = record["order_id"]
        tracking_number = record["tracking_number"]
        carrier = record["carrier"]

        print(
            f"update order {order_id}"
            f"with tracking {tracking_number}"
            f"({carrier})"
        )

def cleanup_tracking_files(local_path, remote_path):

    transport = None
    sftp = None

    try: 
        transport = paramiko.Transport((settings.SFTP_HOST, settings.SFTP_PORT))
        transport.connect(username=settings.SFTP_USER, password=settings.SFTP_PASS,)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        if os.path.exists(local_path):
            os.remove(local_path)
        sftp.remove(remote_path)
    finally:
        if sftp is not None:
            sftp.close()
        if transport is not None:
            transport.close()

def process_tracking():

    files = download_tracking_files()

    for file in files:

        tracking_records = parse_tracking_file(file["local_path"])
        
        update_order_tracking(tracking_records)

        cleanup_tracking_files(
            file["local_path"],
            file["remote_path"]
        )

