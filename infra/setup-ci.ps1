# One-time: an Entra identity for the GitHub evaluation workflow, signed in through OIDC (no secret anywhere).
# GitHub signs a short-lived token for each run; the federated credentials trust only this repo's pull requests and main.
# Its roles come from main.bicep (ciPrincipalId), so run up.ps1 afterwards.
param(
    [Parameter(Mandatory)][string]$Subscription,
    [string]$Repo = 'Ghinduta/foundry-claims-assistant',
    [string]$Name = 'claims-assistant-ci'
)

$appId = az ad app list --display-name $Name --query "[0].appId" --output tsv
if (-not $appId) {
    $appId = az ad app create --display-name $Name --query appId --output tsv
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    az ad sp create --id $appId --output none
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# GitHub's token subject carries the owner and repo ids (owner@id/repo@id), so a renamed or re-created repo of the
# same name doesn't match.
$github = Invoke-RestMethod "https://api.github.com/repos/$Repo"
$subjectRepo = "$($github.owner.login)@$($github.owner.id)/$($github.name)@$($github.id)"

$existing = az ad app federated-credential list --id $appId --query "[].name" --output tsv
foreach ($credential in @(
    @{ name = 'pull-requests'; subject = "repo:${subjectRepo}:pull_request" },
    @{ name = 'main'; subject = "repo:${subjectRepo}:ref:refs/heads/main" }
)) {
    $file = New-TemporaryFile
    @{
        name      = $credential.name
        issuer    = 'https://token.actions.githubusercontent.com'
        subject   = $credential.subject
        audiences = @('api://AzureADTokenExchange')
    } | ConvertTo-Json | Set-Content -Encoding utf8 $file
    if ($existing -contains $credential.name) {
        az ad app federated-credential update --id $appId --federated-credential-id $credential.name --parameters "@$file" --output none
    } else {
        az ad app federated-credential create --id $appId --parameters "@$file" --output none
    }
    $status = $LASTEXITCODE
    Remove-Item $file
    if ($status -ne 0) { exit $status }
}

Write-Host "Add these as GitHub repository variables (Settings > Secrets and variables > Actions > Variables):"
Write-Host "  AZURE_CLIENT_ID       $appId"
Write-Host "  AZURE_TENANT_ID       $(az account show --subscription $Subscription --query tenantId --output tsv)"
Write-Host "  AZURE_SUBSCRIPTION_ID $Subscription"
