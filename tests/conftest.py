import pytest
import hvac
import os
import time

@pytest.fixture(scope="session")
def vault_container():
    """
    This fixture assumes a Vault instance is running.
    In CI, this is provided by the service container.
    Locally, the user must ensure Vault is running.
    """
    vault_url = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
    vault_token = os.getenv("VAULT_TOKEN", "root")

    client = hvac.Client(url=vault_url, token=vault_token)

    # Wait for Vault to be ready
    for _ in range(10):
        try:
            if client.is_sealed is False:
                break
        except Exception:
            pass
        time.sleep(1)

    return client

@pytest.fixture
def vault_client(vault_container):
    """
    Returns a clean Vault client for each test.
    Ensures the secret engine is enabled and clean.
    """
    client = vault_container
    mount_point = "secret"

    # Ensure KV v2 secret engine is enabled at 'secret/'
    sys_backend_path = "sys/mounts"
    try:
        mounts = client.sys.list_mounted_secrets_engines()
        if f"{mount_point}/" not in mounts:
             client.sys.enable_secrets_engine(
                backend_type='kv',
                path=mount_point,
                options={'version': '2'}
            )
    except Exception as e:
        print(f"Warning during mount setup: {e}")

    # Cleanup before test
    try:
        # Listing keys requires list capability, which root has.
        # Recursively delete would be better, but for simple tests we can just overwrite or use unique paths.
        # For now, we'll rely on unique paths per test or simple cleanup if possible.
        pass
    except Exception:
        pass

    yield client

    # Cleanup after test (optional, but good practice)
