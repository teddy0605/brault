# Brault

Brault is a Python package for backing up and restoring KV2 secrets from HashiCorp Vault. It supports both plain text (JSON/YAML) and encrypted backups.

## Features

- Backup all or specific paths from Vault KV2 stores
- Restore secrets to Vault KV2 stores
- Support for both JSON and YAML output formats
- Optional encryption for backup files
- Recursive backup of nested secrets

## Installation

```bash
pip install brault
```

## Usage

### Backup Secrets

```bash
# Backup all secrets from all KV2 stores
brault --url http://vault.example.com:8200 --token your-token-here

# Backup secrets from a specific mount point
brault --url http://vault.example.com:8200 --token your-token-here --mount_point secret

# Backup secrets from a specific path
brault --url http://vault.example.com:8200 --token your-token-here --mount_point secret --path myapp/config

# Backup in YAML format
brault --url http://vault.example.com:8200 --token your-token-here --output_format yaml

# Backup with encryption
brault --url http://vault.example.com:8200 --token your-token-here --encryption_key mysecretpassword
```

### Restore Secrets

```bash
# Restore all secrets from backup
brault --url http://vault.example.com:8200 --token your-token-here --restore

# Restore from a specific backup file
brault --url http://vault.example.com:8200 --token your-token-here --restore --filename my_backup

# Restore from an encrypted backup
brault --url http://vault.example.com:8200 --token your-token-here --restore --encryption_key mysecretpassword
```

## Testing with a Local Vault Instance

You can easily test Brault with a local Vault instance using Docker. Follow these steps to set up an auto-unsealed Vault for testing:

### Prerequisites

- Docker installed on your system

### 1. Start a Local Vault Instance

```bash
docker run --cap-add=IPC_LOCK -e 'VAULT_DEV_ROOT_TOKEN_ID=myroot' -e 'VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200' -p 8200:8200 vault:latest
```

This command will:
- Start a development Vault instance
- Set the root token to `myroot`
- Automatically unseal the Vault
- Expose Vault on port 8200

### 2. Verify Vault is Running

```bash
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='myroot'

# Check Vault status
vault status
```

### 3. Add Some Test Data

```bash
# Enable a KV2 secrets engine if needed
vault secrets enable -path=secret kv-v2

# Add some test secrets
vault kv put secret/myapp/config username=admin password=secret123
vault kv put secret/myapp/database host=localhost port=5432 password=dbsecret
vault kv put secret/anotherapp/api key=apikey123 secret=apisecret456
```

### 4. Test Brault

```bash
# Backup all secrets
brault --url http://127.0.0.1:8200 --token myroot

# View the backup file
cat vault_backup.json

# Test restore to a different mount point
vault secrets enable -path=restored kv-v2
brault --url http://127.0.0.1:8200 --token myroot --restore
```

## License

MIT License