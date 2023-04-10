import argparse
import logging

def parse_arguments():
    parser = argparse.ArgumentParser(description="Vault Backup and Restore Utility")
    parser.add_argument('--url', help="Vault URL", required=True)
    parser.add_argument('--token', help="Vault Token", required=True)
    parser.add_argument('--path', help="Secret Path for Backup or Restore")
    parser.add_argument('--mount_point', help="The mountpoint or keystore to backup")
    parser.add_argument('--output_format', help="Backup File Format (json/yaml)", default='json')
    parser.add_argument('--debug', help="Enable Debug Logging", action='store_true')
    parser.add_argument('--restore', help="Restore Mode", action='store_true')
    parser.add_argument('--filename', help="Backup File Name", default='vault_backup')
    parser.add_argument('--encryption_key', help="Encryption Key for Securing Backup Files")
    args = parser.parse_args()

    if args.path and not args.mount_point:
        parser.error("--path requires --mount_point to be specified.")
    
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')

    return args
