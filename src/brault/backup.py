
import logging

class BackupManager:
    def __init__(self, client, output_format='json'):
        logging.debug("ENTERING BACKUP MANAGER")
        self.client = client
        self.output_format = output_format

    def list_kv_engines(self):
        mounts = self.client.sys.list_mounted_secrets_engines()['data']
        parsed_mounts =  {k[:-1]: v for k, v in mounts.items() if v['type'] == 'kv'}
        return parsed_mounts

    def fetch_secrets(self, mount_point=None, path=None):
        self.secrets = {}
        if mount_point:
            logging.debug(f"Fetching secrets from: mount_point='{mount_point}', path='{path}'")
            self._fetch_secrets_recursive(mount_point, path or '')
        else:
            kv_engines = self.list_kv_engines()
            logging.debug("Ennumerating kv stores")
            for mp in kv_engines.keys():
                logging.debug(f"Fetching secrets from: mount_point='{mp}', path='{path}'")
                self._fetch_secrets_recursive(mp, path or '')
        return self.secrets

    def _fetch_secrets_recursive(self, mount_point, path):
        try:
            secrets_list = self.client.secrets.kv.v2.list_secrets(path=path, mount_point=mount_point)
            logging.debug(f"Listing secrets at: {mount_point}{path}, found: {secrets_list['data']['keys']}")
            for key in secrets_list['data'].get('keys', []):
                full_path = f"{path}/{key}"
                # hvac list_secrets keys often end with / for folders, but let's be robust
                # If path was empty, full_path starts with /, strip it
                if path == '':
                    full_path = key

                if key.endswith('/'):
                    logging.debug(f"{full_path} is a folder, going deeper.")
                    self._fetch_secrets_recursive(mount_point, full_path.rstrip('/'))
                else:
                    logging.debug(f"{full_path} is a secret, fetching contents.")
                    self._fetch_secret(mount_point, full_path)
        except Exception:
            # If listing fails, it might be a direct path to a secret
            try:
                # remove leading slash if present, hvac doesn't like it sometimes
                clean_path = path.lstrip('/')
                logging.debug(f"Listing failed, attempting to fetch as single secret: {clean_path}")
                self._fetch_secret(mount_point, clean_path)
            except Exception as e:
                logging.error(f"Failed to fetch secrets from {mount_point}/{path}. It's neither a listable path nor a readable secret. Error: {e}")

    def _fetch_secret(self, mount_point, path):
        try:
            secret = self.client.secrets.kv.v2.read_secret_version(path=path, mount_point=mount_point)
            data = secret['data']['data']
            parts = path.lstrip('/').split('/')
            current_dict = self.secrets.setdefault(mount_point, {})
            for part in parts[:-1]:
                current_dict = current_dict.setdefault(part, {})
            current_dict[parts[-1]] = data
        except Exception as e:
            logging.error(f"Failed to fetch secret from {mount_point}/{path}: {e}")