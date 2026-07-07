import csv
import os
import posixpath
from pathlib import Path

import paramiko

from Core.config import settings


TRACKING_DOWNLOAD_DIR = Path("tracking_downloads")
TRACKING_DOWNLOAD_DIR.mkdir(exist_ok=True)


def _connect_sftp():
    """
    Creates and returns an authenticated SFTP connection.

    Returns:
        tuple[paramiko.Transport, paramiko.SFTPClient]
    """

    transport = paramiko.Transport(
        (settings.SFTP_HOST, settings.SFTP_PORT)
    )

    transport.connect(
        username=settings.SFTP_USER,
        password=settings.SFTP_PASS,
    )

    sftp = paramiko.SFTPClient.from_transport(transport)

    return transport, sftp

def download_tracking_files() -> list[dict]:
    """
    Downloads every CSV file from the warehouse tracking folder.
    """
    downloaded_files = []
    transport = None
    sftp = None

    try:
        transport, sftp = _connect_sftp()
        tracking_dir = settings.SFTP_TRACKING_DIR

        # REPAIR: Wrap listdir in a try/except to handle missing remote folders gracefully
        try:
            files = sftp.listdir(tracking_dir)
        except IOError:
            print(f"[TRACKING] Remote directory '{tracking_dir}' not found on warehouse server. Skipping.")
            return [] # Safely return an empty list

        for filename in files:
            if not filename.lower().endswith(".csv"):
                continue

            remote_path = posixpath.join(
                tracking_dir,
                filename,
            )
            local_path = TRACKING_DOWNLOAD_DIR / filename

            sftp.get(
                remote_path,
                str(local_path),
            )

            downloaded_files.append(
                {
                    "filename": filename,
                    "local_path": str(local_path),
                    "remote_path": remote_path,
                }
            )
            print(f"[TRACKING] Downloaded {filename}")

        return downloaded_files

    finally:
        if sftp:
            sftp.close()
        if transport:
            transport.close()


def parse_tracking_file(local_path: str) -> list[dict]:
    """
    Parses one warehouse tracking CSV.

    Expected columns:

    order_id
    tracking_number
    carrier
    """

    tracking_records = []

    with open(
        local_path,
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            order_id = row.get("order_id")
            tracking_number = row.get("tracking_number")
            carrier = row.get("carrier")

            if (
                not order_id
                or not tracking_number
                or not carrier
            ):
                continue

            tracking_records.append(
                {
                    "order_id": order_id.strip(),
                    "tracking_number": tracking_number.strip(),
                    "carrier": carrier.strip(),
                }
            )

    return tracking_records


def cleanup_tracking_file(
    local_path: str,
    remote_path: str,
) -> None:
    """
    Removes processed tracking files
    from both local storage and warehouse.
    """

    transport = None
    sftp = None

    try:

        transport, sftp = _connect_sftp()

        if os.path.exists(local_path):
            os.remove(local_path)

        sftp.remove(remote_path)

        print(f"[TRACKING] Removed {remote_path}")

    finally:

        if sftp:
            sftp.close()

        if transport:
            transport.close()


def process_tracking():
    """
    Downloads and parses tracking files.

    Returns:

    [
        {
            "file": "...",
            "records": [...]
        }
    ]

    Database updates are handled
    by tracking_worker.py.
    """

    processed = []

    files = download_tracking_files()

    for file in files:

        records = parse_tracking_file(
            file["local_path"]
        )

        processed.append(
            {
                "file": file,
                "records": records,
            }
        )

    return processed