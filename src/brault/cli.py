from hvac import Client
import logging
import requests
import json
import yaml
from .utils import parse_arguments
from .encryption import EncryptionManager
from .files import FilesManager
from .backup import BackupManager
from .restore import RestoreManager

def main():
    args = parse_arguments()
    
    client = Client(url=args.url, token=args.token)
    try:
        if not client.is_authenticated():
            logging.error("Failed to authenticate to Vault.")
            return
    except requests.exceptions.ConnectionError:
        logging.error(f"Failed to connect to Vault at {args.url}.")
        return
    files_manager = FilesManager(args.filename, args.output_format)

    if args.restore:
        try:
            file_data = files_manager.read_file()
            if args.encryption_key:
                decrypted_data_bytes = EncryptionManager(args.encryption_key).decrypt_data(file_data)
                decrypted_data = json.loads(decrypted_data_bytes) if args.output_format == 'json' else yaml.safe_load(decrypted_data_bytes)
            else:
                try:
                    decrypted_data = json.loads(file_data.decode('utf-8')) if args.output_format == 'json' else yaml.safe_load(file_data.decode('utf-8'))
                except ValueError:
                    logging.error("Failed to deserialize the backup file. If the backup file is encrypted, provide the key using --encryption_key.")
                    raise
            RestoreManager(client, args.mount_point).restore_secrets(decrypted_data)
            logging.info("Restore complete!")
        except Exception as e:
            logging.error(f"Restore failed: {e}")

    else:
        try:
            backup_manager = BackupManager(client, args.output_format)
            vault_data = backup_manager.fetch_secrets(args.mount_point, args.path)
            if args.encryption_key:
                serialized_data = json.dumps(vault_data) if args.output_format == 'json' else yaml.dump(vault_data)
                encrypted_data = EncryptionManager(args.encryption_key).encrypt_data(serialized_data)
                files_manager.write_file(encrypted_data)
                logging.info("Backup completed to encrypted file.")
            else:
                files_manager.write_file(vault_data)
                logging.info("Backup completed to non-encrypted file.")
        except Exception as e:
            logging.error(f"Backup failed: {e}")

if __name__ == "__main__":
    main()
