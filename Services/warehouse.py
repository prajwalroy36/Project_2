import os
import paramiko

from Core.config import settings


def upload_via_sftp(local_file_path: str) -> str:
    """
    Uploads a CSV file to the warehouse.

    Returns
    -------
    str
        The uploaded filename on the warehouse.

    Raises
    ------
    Exception
        Any upload related exception.
    """

    transport = None
    sftp = None

    try:

        transport = paramiko.Transport(
            (
                settings.SFTP_HOST,
                settings.SFTP_PORT,
            )
        )

        transport.connect(
            username=settings.SFTP_USERNAME,
            password=settings.SFTP_PASSWORD,
        )

        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_filename = os.path.basename(local_file_path)

        remote_path = (
            settings.SFTP_REMOTE_DIRECTORY.rstrip("/")
            + "/"
            + remote_filename
        )

        sftp.put(local_file_path, remote_path)

        return remote_filename

    except paramiko.AuthenticationException:

        raise Exception(
            "Warehouse login failed. Check username or password."
        )

    except FileNotFoundError:

        raise Exception(
            "CSV file does not exist."
        )

    except TimeoutError:

        raise Exception(
            "Warehouse connection timed out."
        )

    except Exception as e:

        raise Exception(
            f"Warehouse upload failed : {str(e)}"
        )

    finally:

        if sftp is not None:
            sftp.close()

        if transport is not None:
            transport.close()