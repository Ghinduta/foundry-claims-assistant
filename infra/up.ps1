# Create the resource group and deploy main.bicep. Run at the start of a session.
# -Subscription is required so a deployment never lands in whatever subscription az happens to default to.
param(
    [Parameter(Mandatory)][string]$Subscription,
    [string]$ResourceGroup = 'rg-claims-assistant',
    [string]$Location = 'swedencentral',
    [string]$SearchLocation = 'northeurope' # swedencentral ran out of AI Search capacity (InsufficientResourcesAvailable)
)

az group create --subscription $Subscription --name $ResourceGroup --location $Location --output none
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$me = az ad signed-in-user show --query id --output tsv
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Empty until infra/setup-ci.ps1 has run once; then the GitHub evaluation gets its roles on every deploy.
$ci = az ad sp list --display-name claims-assistant-ci --query "[0].id" --output tsv

az deployment group create `
    --subscription $Subscription `
    --resource-group $ResourceGroup `
    --template-file "$PSScriptRoot/main.bicep" `
    --parameters developerPrincipalId=$me searchLocation=$SearchLocation ciPrincipalId=$ci `
    --query properties.outputs `
    --output json
exit $LASTEXITCODE
