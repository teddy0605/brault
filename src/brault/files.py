import logging
import json
import yaml

class FilesManager:
    def __init__(self, filename='vault_backup', output_format='json'):
        logging.debug("ENTERING FILE MANAGER")
        self.output_format = output_format
        self.filename = f"{filename}.{output_format}"

    def read_file(self):
        try:
            with open(self.filename, 'rb') as file:
                file_content = file.read()
                logging.info("Backup file read successfully.")
                return file_content
        except Exception as e:
            logging.error(f"Failed to read file {self.filename}: {e}")
            raise

    def write_file(self, data):
        if not data:
            logging.info("Nothing to write. Skipping file creation.")
            return
        try:
            if isinstance(data, bytes):
                content_to_write = data
            else:
                content_to_write = json.dumps(data, indent=4) if self.output_format == 'json' else yaml.dump(data)
            with open(self.filename, 'wb' if isinstance(data, bytes) else 'w') as file:
                file.write(content_to_write)
                logging.info("Backup written to file.")
        except Exception as e:
            logging.error(f"Failed to write to file {self.filename}: {e}")
            raise
