import logging

class RestoreManager:
    def __init__(self, client, mount_point=None):
        logging.debug("ENTERING RESTORE MANAGER")
        self.client = client
        self.mount_point = mount_point

    def list_kv_engines(self):
        mounts = self.client.sys.list_mounted_secrets_engines()['data']
        parsed_mounts = {k[:-1]: v for k, v in mounts.items() if v['type'] == 'kv'}
        return parsed_mounts

    def restore_secrets(self, secrets):
        logging.info("Starting secrets restore.")
        existing_mounts = self.list_kv_engines()
        logging.debug(f"Found the following mountpoints : {existing_mounts.keys()}")
        for backup_mount_point, paths in secrets.items():
            logging.debug(f"Mount point is {backup_mount_point} and paths are {paths}")
            
            if self.mount_point and backup_mount_point != self.mount_point:
                logging.warning(f"Skipping restore for '{backup_mount_point}' as it does not match the specified mount point '{self.mount_point}'.")
                continue

            if backup_mount_point not in existing_mounts:
                logging.warning(f"Mount point '{backup_mount_point}' does not exist. Skipping...")
                continue
            self.restore_nested_secrets(backup_mount_point, '', paths)
    
    def restore_nested_secrets(self, mount_point, current_path, secrets_data):
        for key, value in secrets_data.items():
            if not isinstance(value, dict):
                secret_data = {key: value}
                final_path = current_path
            else:
                if all(not isinstance(sub_value, dict) for sub_value in value.values()):
                    secret_data = value
                    final_path = f"{current_path}/{key}".strip('/')
                else:
                    self.restore_nested_secrets(mount_point, f"{current_path}/{key}".strip('/'), value)
                    continue
            logging.debug(f"Restoring secret at path: {final_path} with data: {secret_data}")
            try:
                self.client.secrets.kv.v2.create_or_update_secret(path=final_path, secret=secret_data, mount_point=mount_point)
                logging.info(f"Restored secret at {mount_point}/{final_path}")
            except Exception as e:
                logging.error(f"Failed to restore secret at {mount_point}/{final_path}: {e}")




