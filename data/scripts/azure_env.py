"""Endpoints of the deployed infrastructure, read from the outputs of the last `infra/up.ps1` run.

Uses the az CLI login, so it targets whichever subscription `az account show` reports.
"""

import json
import shutil
import subprocess
from dataclasses import dataclass
from urllib.parse import urlparse

RESOURCE_GROUP = "rg-claims-assistant"


def _az(*args: str):
    out = subprocess.run([shutil.which("az"), *args, "--output", "json"], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


@dataclass(frozen=True)
class AzureEnv:
    subscription_id: str
    foundry_name: str
    project_endpoint: str
    search_connection_name: str
    search_endpoint: str
    storage_blob_endpoint: str

    @property
    def openai_endpoint(self) -> str:
        return f"https://{self.foundry_name}.openai.azure.com"

    @property
    def storage_resource_id(self) -> str:
        account = urlparse(self.storage_blob_endpoint).hostname.split(".")[0]
        return (f"/subscriptions/{self.subscription_id}/resourceGroups/{RESOURCE_GROUP}"
                f"/providers/Microsoft.Storage/storageAccounts/{account}")


def load() -> AzureEnv:
    outputs = _az("deployment", "group", "show", "--resource-group", RESOURCE_GROUP, "--name", "main",
                  "--query", "properties.outputs")
    return AzureEnv(
        subscription_id=_az("account", "show", "--query", "id"),
        foundry_name=outputs["foundryName"]["value"],
        project_endpoint=outputs["projectEndpoint"]["value"],
        search_connection_name=outputs["searchConnectionName"]["value"],
        search_endpoint=outputs["searchEndpoint"]["value"],
        storage_blob_endpoint=outputs["storageBlobEndpoint"]["value"],
    )
