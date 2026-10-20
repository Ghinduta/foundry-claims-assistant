// M1: everything the claims assistant needs in Azure, keyless.
// Deploy:   ./infra/up.ps1      Remove (end of each session): ./infra/down.ps1

@description('Region for all resources. Must offer the chat model on the chosen deployment type and AI Search Basic.')
param location string = resourceGroup().location

@description('Region for AI Search alone, for when the main region has no Search capacity. It calls Foundry and Storage across regions.')
param searchLocation string = location

@description('Object id of the person running scripts locally (az ad signed-in-user show --query id -o tsv).')
param developerPrincipalId string

@description('Object id of the GitHub Actions service principal (infra/setup-ci.ps1), or empty for no CI access.')
param ciPrincipalId string = ''

@description('Global = cheapest, routed anywhere. DataZone = processed inside the EU/US data zone.')
@allowed(['GlobalStandard', 'DataZoneStandard'])
param deploymentType string = 'GlobalStandard'

@description('Thousands of tokens per minute for each model deployment.')
param chatCapacity int = 50
param embeddingCapacity int = 50

var suffix = uniqueString(resourceGroup().id)
var foundryName = 'claims-foundry-${suffix}'

var roles = {
  storageBlobDataReader: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  cognitiveServicesOpenAIUser: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  foundryUser: '53ca6127-db72-4b80-b1b0-d745d6d5456d'
  searchIndexDataReader: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
  searchIndexDataContributor: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  searchServiceContributor: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  reader: 'acdd72a7-3843-4bc2-b9e0-a1a3a3a1b67e'
}

// ---------- Foundry: the resource holds deployments and guardrails; the project holds agents and evaluations.

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: foundryName
  location: location
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    allowProjectManagement: true
    customSubDomainName: foundryName // Entra ID auth needs a custom subdomain endpoint
    disableLocalAuth: true // no API keys: every call must carry an Entra token
    publicNetworkAccess: 'Enabled'
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: foundry
  name: 'claims-assistant'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {}
}

// Our own guardrails instead of Microsoft.DefaultV2. Prompts stay at Medium so customers can describe accidents and
// injuries; answers go to Low because they're customer-facing. IndirectAttack only scans documents embedded in the
// prompt in the documented format. Creating the policy needs the spaced names; Azure then stores them without spaces.
resource contentFilter 'Microsoft.CognitiveServices/accounts/raiPolicies@2025-06-01' = {
  parent: foundry
  name: 'claims-assistant-filter'
  properties: {
    basePolicyName: 'Microsoft.DefaultV2'
    mode: 'Blocking'
    contentFilters: [
      for filter in [
        { name: 'Hate', source: 'Prompt', severityThreshold: 'Medium' }
        { name: 'Sexual', source: 'Prompt', severityThreshold: 'Medium' }
        { name: 'Violence', source: 'Prompt', severityThreshold: 'Medium' }
        { name: 'Selfharm', source: 'Prompt', severityThreshold: 'Medium' }
        { name: 'Hate', source: 'Completion', severityThreshold: 'Low' }
        { name: 'Sexual', source: 'Completion', severityThreshold: 'Low' }
        { name: 'Violence', source: 'Completion', severityThreshold: 'Low' }
        { name: 'Selfharm', source: 'Completion', severityThreshold: 'Low' }
        { name: 'Jailbreak', source: 'Prompt' }
        { name: 'Indirect Attack', source: 'Prompt' }
        { name: 'Protected Material Text', source: 'Completion' }
        { name: 'Protected Material Code', source: 'Completion' }
      ]: union(filter, { enabled: true, blocking: true })
    ]
  }
  dependsOn: [project] // the account accepts one change at a time; parallel children fail with RequestConflict
}

// gpt-4.1-mini is Deprecated for new subscriptions, and a new trial has 0 quota for gpt-5.4-mini.
resource chat 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: 'gpt-5-mini'
  sku: { name: deploymentType, capacity: chatCapacity }
  properties: {
    model: { format: 'OpenAI', name: 'gpt-5-mini', version: '2025-08-07' }
    raiPolicyName: contentFilter.name
  }
}

resource embedding 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: 'text-embedding-3-small'
  sku: { name: deploymentType, capacity: embeddingCapacity }
  properties: {
    model: { format: 'OpenAI', name: 'text-embedding-3-small', version: '1' }
  }
  dependsOn: [chat] // deployments on one account must be created one at a time
}

// ---------- Storage: source files for the indexer and uploads.

resource storage 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name: 'claimsst${suffix}'
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    allowSharedKeyAccess: false // no account keys or SAS from keys: Entra only
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
  }
}

resource blobs 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' = {
  parent: storage
  name: 'default'
}

resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' = [
  for name in ['policy-docs', 'claim-forms', 'photos']: {
    parent: blobs
    name: name
  }
]

// ---------- AI Search: Basic, because Free can't use a managed identity for the indexer and vectorizer.

resource search 'Microsoft.Search/searchServices@2025-05-01' = {
  name: 'claims-search-${suffix}'
  location: searchLocation
  sku: { name: 'basic' }
  identity: { type: 'SystemAssigned' }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'Default'
    disableLocalAuth: true // RBAC only, no admin or query keys
    semanticSearch: 'free'
    publicNetworkAccess: 'enabled'
  }
}

// The agent's knowledge-search tool reaches the index through this connection, signed in as the project's identity.
resource searchConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = {
  parent: project
  name: 'claims-search'
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${search.name}.search.windows.net'
    authType: 'AAD' // no key stored in the connection
    metadata: {
      ApiType: 'Azure'
      ResourceId: search.id
      location: search.location
    }
  }
  dependsOn: [embedding] // one change at a time on the Foundry account
}

// ---------- Monitoring: App Insights stores traces in a Log Analytics workspace.

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'claims-logs-${suffix}'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'claims-appi-${suffix}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

// ---------- Role assignments. Each grants one identity one data-plane permission on one resource.

// The search service's own identity: the indexer reads blobs; the embedding skill and vectorizer call the model.
resource searchReadsBlobs 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, search.id, roles.storageBlobDataReader)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.storageBlobDataReader)
    principalId: search.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource searchCallsEmbeddings 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, search.id, roles.cognitiveServicesOpenAIUser)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.cognitiveServicesOpenAIUser)
    principalId: search.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// The project's identity: the agent's knowledge-search tool reads the index and its schema.
resource projectReadsIndex 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, project.id, roles.searchIndexDataReader)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.searchIndexDataReader)
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource projectReadsSearchService 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, project.id, roles.searchServiceContributor)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.searchServiceContributor)
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// You, through DefaultAzureCredential: the same Python code later runs as the app's managed identity.

// Call models and create agents in the project.
resource developerUsesFoundry 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, developerPrincipalId, roles.foundryUser)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.foundryUser)
    principalId: developerPrincipalId
    principalType: 'User'
  }
}

// Upload the data files.
resource developerWritesBlobs 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, developerPrincipalId, roles.storageBlobDataContributor)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.storageBlobDataContributor)
    principalId: developerPrincipalId
    principalType: 'User'
  }
}

// Load and query index documents.
resource developerWritesIndex 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, developerPrincipalId, roles.searchIndexDataContributor)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.searchIndexDataContributor)
    principalId: developerPrincipalId
    principalType: 'User'
  }
}

// Create indexes, indexers, skillsets (control plane of the search service).
resource developerManagesSearch 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, developerPrincipalId, roles.searchServiceContributor)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.searchServiceContributor)
    principalId: developerPrincipalId
    principalType: 'User'
  }
}

// GitHub Actions, signed in through OIDC (no secret): runs the agent and the judge model, and reads the deployment
// outputs for the endpoints. It can't change the agent or the infrastructure.
resource ciUsesFoundry 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(ciPrincipalId)) {
  scope: foundry
  name: guid(foundry.id, ciPrincipalId, roles.foundryUser)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.foundryUser)
    principalId: ciPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource ciReadsDeployment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(ciPrincipalId)) {
  name: guid(resourceGroup().id, ciPrincipalId, roles.reader)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.reader)
    principalId: ciPrincipalId
    principalType: 'ServicePrincipal'
  }
}

output foundryName string = foundry.name
output foundryEndpoint string = foundry.properties.endpoint
output projectEndpoint string = 'https://${foundryName}.services.ai.azure.com/api/projects/${project.name}'
output searchConnectionName string = searchConnection.name
output searchEndpoint string = 'https://${search.name}.search.windows.net'
output storageBlobEndpoint string = storage.properties.primaryEndpoints.blob
output appInsightsConnectionString string = appInsights.properties.ConnectionString
