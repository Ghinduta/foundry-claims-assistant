# Delete everything billed hourly. Run at the end of a session; up.ps1 recreates it.
param(
    [Parameter(Mandatory)][string]$Subscription,
    [string]$ResourceGroup = 'rg-claims-assistant'
)

$foundry = az cognitiveservices account list --subscription $Subscription --resource-group $ResourceGroup `
    --query "[0].{name:name, location:location}" --output json | ConvertFrom-Json

az group delete --subscription $Subscription --name $ResourceGroup --yes
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Deleted Foundry accounts are soft-deleted for 48 hours and block reusing the name; purge frees it.
if ($foundry) {
    az cognitiveservices account purge --subscription $Subscription --name $foundry.name --resource-group $ResourceGroup --location $foundry.location
}
exit $LASTEXITCODE
