import os

import paramiko

from Core.config import settings


def upload_via_sftp(local_file_path: str) -> str:
    """
    Uploads a CSV file to the warehouse SFTP inbox.
    """
    transport = None
    sftp = None

    try:
        transport = paramiko.Transport((settings.SFTP_HOST, settings.SFTP_PORT))
        transport.connect(username=settings.SFTP_USER, password=settings.SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_filename = os.path.basename(local_file_path)
        remote_path = f"{settings.SFTP_UPLOAD_DIR.rstrip('/')}/{remote_filename}"
        sftp.put(local_file_path, remote_path)

        return remote_filename

    except paramiko.AuthenticationException as exc:
        raise Exception("Warehouse login failed. Check SFTP_USER or SFTP_PASS.") from exc
    except FileNotFoundError as exc:
        raise Exception("CSV file does not exist.") from exc
    except TimeoutError as exc:
        raise Exception("Warehouse connection timed out.") from exc
    except Exception as exc:
        raise Exception(f"Warehouse upload failed: {exc}") from exc
    finally:
        if sftp is not None:
            sftp.close()
        if transport is not None:
            transport.close()
