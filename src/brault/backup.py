
import logging

try:
    from hvac.exceptions import InvalidPath
except Exception:  # pragma: no cover - hvac import guarded for runtime envs
    InvalidPath = None

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
                if key.endswith('/'):
                    logging.debug(f"{full_path} is a folder, going deeper.")
                    self._fetch_secrets_recursive(mount_point, full_path.rstrip('/'))
                else:
                    logging.debug(f"{full_path} is a secret, fetching contents.")
                    self._fetch_secret(mount_point, full_path)
        except Exception as e:
            is_invalid_path = False
            if InvalidPath is not None and isinstance(e, InvalidPath):
                is_invalid_path = True
            elif getattr(e, "status_code", None) == 404:
                is_invalid_path = True
            elif "404" in str(e):
                is_invalid_path = True

            if is_invalid_path:
                if path:
                    logging.debug(
                        f"{mount_point}/{path} looks like a leaf; fetching the secret directly."
                    )
                    self._fetch_secret(mount_point, path)
                else:
                    logging.error("This path does not exist or is a leaf (key-value pair)")
            else:
                logging.error(f"Failed to fetch secrets from {mount_point}/{path}: {e}")

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