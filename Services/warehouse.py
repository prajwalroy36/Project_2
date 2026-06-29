import os
import paramiko
from Core.config import settings

def upload_via_sftp(local_file_path:str):
    # in production these  parameter will be pulled from your .env file
    HOST = settings.SFTP_HOST
    PORT = settings.SFTP_PORT
    USER = settings.SFTP_USERNAME
    PASSWORD = settings.SFTP_PASSWORD
    

    transport = paramiko.Transport((HOST, PORT))
    transport.banner_timeout = 10
    transport.auth_timeout = 10
    sftp = None
    try:
        print(f"CONNECTING TO {HOST}:{PORT}")
        transport.connect(username=USER,password=PASSWORD)

        print(f"CONNECTED TO WAREHOUSE!")
        sftp = paramiko.SFTPClient.from_transport(transport)

        

    #destination directory file path definition
        remote_file_name = os.path.basename(local_file_path)
        remote_file_path = ( f"{settings.SFTP_REMOTE_DIRECTORY}/{remote_file_name}")

        print(f"uploading {remote_file_name} to {remote_file_path}")



    #execute secure transfer pipeline
    
        sftp.put(local_file_path, remote_file_path)

        print(f"UPLOAD COMPLETE!")
    finally:
        if sftp is not None:
            sftp.close()
        if transport is not None:
            transport.close()