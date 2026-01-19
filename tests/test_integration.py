import os
import json
import pytest
from brault.cli import main as brault_main
from unittest.mock import patch
import sys

def test_backup_and_restore_integration(vault_client, tmp_path):
    """
    Integration test that:
    1. Writes secrets to Vault.
    2. Uses brault to backup.
    3. Clears Vault.
    4. Uses brault to restore.
    5. Verifies secrets.
    """
    mount_point = "secret"
    secret_path = "test/integration/app1"
    secret_data = {"foo": "bar", "api_key": "12345"}

    # 1. Write secrets
    vault_client.secrets.kv.v2.create_or_update_secret(
        mount_point=mount_point,
        path=secret_path,
        secret=secret_data
    )

    # Verify write
    read_response = vault_client.secrets.kv.v2.read_secret_version(
        mount_point=mount_point,
        path=secret_path
    )
    assert read_response['data']['data'] == secret_data

    # Define backup file path
    backup_file = tmp_path / "backup.json"

    # 2. Run Brault Backup
    # Mock sys.argv
    backup_args = [
        "brault",
        "--url", vault_client.url,
        "--token", vault_client.token,
        "--mount_point", mount_point,
        "--path", secret_path,
        "--filename", str(backup_file).replace(".json", ""), # brault adds extension
        "--output_format", "json"
    ]

    with patch.object(sys, 'argv', backup_args):
        brault_main()

    assert backup_file.exists()

    # 3. Clear Vault (simulate disaster)
    # Deleting the metadata destroys all versions
    vault_client.secrets.kv.v2.delete_metadata_and_all_versions(
        mount_point=mount_point,
        path=secret_path
    )

    # Verify deletion
    with pytest.raises(Exception): # hvac raises InvalidPath or similar on missing secret
        vault_client.secrets.kv.v2.read_secret_version(
            mount_point=mount_point,
            path=secret_path
        )

    # 4. Run Brault Restore
    restore_args = [
        "brault",
        "--url", vault_client.url,
        "--token", vault_client.token,
        "--mount_point", mount_point,
        "--filename", str(backup_file).replace(".json", ""),
        "--restore"
    ]

    with patch.object(sys, 'argv', restore_args):
        brault_main()

    # 5. Verify Restore
    read_response = vault_client.secrets.kv.v2.read_secret_version(
        mount_point=mount_point,
        path=secret_path
    )
    assert read_response['data']['data'] == secret_data

def test_encrypted_backup_restore(vault_client, tmp_path):
    """
    Test encrypted backup and restore flow.
    """
    mount_point = "secret"
    secret_path = "test/integration/secure"
    secret_data = {"password": "super_secret_password"}
    encryption_key = "mysecretkey"

    # Write secret
    vault_client.secrets.kv.v2.create_or_update_secret(
        mount_point=mount_point,
        path=secret_path,
        secret=secret_data
    )

    backup_file = tmp_path / "encrypted_backup" # brault might add extension? Let's check logic.
    # brault/files.py usually adds extension based on format.

    # Backup with encryption
    backup_args = [
        "brault",
        "--url", vault_client.url,
        "--token", vault_client.token,
        "--mount_point", mount_point,
        "--path", secret_path,
        "--filename", str(backup_file),
        "--encryption_key", encryption_key
    ]

    with patch.object(sys, 'argv', backup_args):
        brault_main()

    # Check that file exists (files.py likely adds .json by default if format is json)
    expected_file = tmp_path / "encrypted_backup.json"
    assert expected_file.exists()

    # Verify file content is NOT plain JSON
    with open(expected_file, 'r') as f:
        content = f.read()
        assert "super_secret_password" not in content

    # Clear Vault
    vault_client.secrets.kv.v2.delete_metadata_and_all_versions(
        mount_point=mount_point,
        path=secret_path
    )

    # Restore
    restore_args = [
        "brault",
        "--url", vault_client.url,
        "--token", vault_client.token,
        "--mount_point", mount_point,
        "--filename", str(backup_file),
        "--encryption_key", encryption_key,
        "--restore"
    ]

    with patch.object(sys, 'argv', restore_args):
        brault_main()

    # Verify
    read_response = vault_client.secrets.kv.v2.read_secret_version(
        mount_point=mount_point,
        path=secret_path
    )
    assert read_response['data']['data'] == secret_data
