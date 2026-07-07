import csv

from pydantic import ValidationError

from Core.config import settings
from Schemas.tracking import TrackingRecord
from Services.logger import logger


TRACKING_DOWNLOAD_DIR = __import__("pathlib").Path("tracking_downloads")
TRACKING_DOWNLOAD_DIR.mkdir(exist_ok=True)


def _connect_sftp():
    import paramiko

    transport = paramiko.Transport((settings.SFTP_HOST, settings.SFTP_PORT))
    transport.connect(username=settings.SFTP_USER, password=settings.SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)
    return transport, sftp


def download_tracking_files() -> list[dict]:
    downloaded_files = []
    transport = None
    sftp = None

    try:
        transport, sftp = _connect_sftp()
        tracking_dir = settings.SFTP_TRACKING_DIR

        try:
            files = sftp.listdir(tracking_dir)
        except OSError:
            logger.warning("Remote tracking directory '%s' not found. Skipping.", tracking_dir)
            return []

        for filename in files:
            if not filename.lower().endswith(".csv"):
                continue

            import posixpath

            remote_path = posixpath.join(tracking_dir, filename)
            local_path = TRACKING_DOWNLOAD_DIR / filename
            sftp.get(remote_path, str(local_path))

            downloaded_files.append({
                "filename": filename,
                "local_path": str(local_path),
                "remote_path": remote_path,
            })
            logger.info("Downloaded tracking file %s", filename)

        return downloaded_files

    finally:
        if sftp:
            sftp.close()
        if transport:
            transport.close()


def parse_tracking_file(local_path: str) -> list[dict]:
    """
    Parses one warehouse tracking CSV using the strict TrackingRecord contract.
    Invalid rows are skipped and logged.
    """
    tracking_records = []

    with open(local_path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row_number, row in enumerate(reader, start=2):
            try:
                record = TrackingRecord.model_validate(row)
                tracking_records.append(record.model_dump())
            except ValidationError as exc:
                logger.warning(
                    "Skipping invalid tracking row %s in %s: %s",
                    row_number,
                    local_path,
                    exc.errors(),
                )

    return tracking_records


def cleanup_tracking_file(local_path: str, remote_path: str) -> None:
    import os

    transport = None
    sftp = None

    try:
        transport, sftp = _connect_sftp()

        if os.path.exists(local_path):
            os.remove(local_path)

        sftp.remove(remote_path)
        logger.info("Removed tracking file %s", remote_path)

    finally:
        if sftp:
            sftp.close()
        if transport:
            transport.close()


def process_tracking():
    """
    Downloads and parses tracking files.
    Database updates are handled by tracking_worker.py.
    """
    processed = []
    files = download_tracking_files()

    for file in files:
        records = parse_tracking_file(file["local_path"])
        processed.append({"file": file, "records": records})

    return processed
