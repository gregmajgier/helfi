targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
@description('Name of the azd environment, used to derive a unique resource token')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@secure()
@description('JWT signing secret for the backend API (production)')
param jwtSecret string

@secure()
@description('Anthropic API key (optional). Leave blank to disable meal-photo nutrition estimation.')
param anthropicApiKey string = ''

@description('Google OAuth client ID (optional)')
param googleOauthClientId string = ''

@description('Apple OAuth bundle ID (optional)')
param appleOauthBundleId string = ''

@description('Full container image reference, e.g. ghcr.io/gregmajgier/helfi-api:latest')
param apiContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

var tags = {
  'azd-env-name': environmentName
}

module resources './modules/resources.bicep' = {
  name: 'resources'
  params: {
    environmentName: environmentName
    location: location
    jwtSecret: jwtSecret
    anthropicApiKey: anthropicApiKey
    googleOauthClientId: googleOauthClientId
    appleOauthBundleId: appleOauthBundleId
    apiContainerImage: apiContainerImage
    tags: tags
  }
}

output AZURE_CONTAINER_APPS_ENVIRONMENT_ID string = resources.outputs.containerAppsEnvironmentId
output SERVICE_API_NAME string = resources.outputs.apiName
output API_BASE_URL string = resources.outputs.apiBaseUrl
output AZURE_COSMOS_ENDPOINT string = resources.outputs.cosmosEndpoint
