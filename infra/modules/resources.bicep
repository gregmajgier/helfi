targetScope = 'resourceGroup'

param environmentName string
param location string

@secure()
param jwtSecret string

@secure()
param anthropicApiKey string

param googleOauthClientId string
param appleOauthBundleId string
param tags object

@description('Full container image reference, e.g. ghcr.io/gregmajgier/helfi-api:latest')
param apiContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

var resourceToken = take(uniqueString(subscription().id, resourceGroup().id, environmentName), 6)
var cosmosDatabaseName = 'health_app'

var baseSecrets = [
  { name: 'jwt-secret', value: jwtSecret }
  { name: 'cosmos-connection-string', value: cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString }
]
var anthropicSecret = !empty(anthropicApiKey) ? [
  { name: 'anthropic-api-key', value: anthropicApiKey }
] : []
var containerSecrets = concat(baseSecrets, anthropicSecret)

var baseEnv = [
  { name: 'ENVIRONMENT', value: 'production' }
  { name: 'DB_BACKEND', value: 'cosmos' }
  { name: 'COSMOS_DATABASE_NAME', value: cosmosDatabaseName }
  { name: 'JWT_SECRET', secretRef: 'jwt-secret' }
  { name: 'COSMOS_CONNECTION_STRING', secretRef: 'cosmos-connection-string' }
  { name: 'GOOGLE_OAUTH_CLIENT_ID', value: googleOauthClientId }
  { name: 'APPLE_OAUTH_BUNDLE_ID', value: appleOauthBundleId }
]
var anthropicEnv = !empty(anthropicApiKey) ? [
  { name: 'ANTHROPIC_API_KEY', secretRef: 'anthropic-api-key' }
] : []
var containerEnv = concat(baseEnv, anthropicEnv)

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${environmentName}-${resourceToken}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-${environmentName}-${resourceToken}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: 'cosmos-${environmentName}-${resourceToken}'
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: cosmosDatabaseName
  properties: {
    resource: {
      id: cosmosDatabaseName
    }
  }
}

// Image is pulled from GitHub Container Registry (ghcr.io), not Azure Container
// Registry, to avoid ACR's fixed monthly fee. Assumes the GHCR package is public
// (set visibility to Public once in GitHub package settings after the first push) —
// no registries/pull-secret block is needed for a public image.
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-api-${environmentName}-${resourceToken}'
  location: location
  tags: union(tags, { 'azd-service-name': 'api' })
  properties: {
    environmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      secrets: containerSecrets
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiContainerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: containerEnv
          probes: [
            {
              type: 'liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'startup'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 0
              periodSeconds: 10
              failureThreshold: 30
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

output containerAppsEnvironmentId string = containerAppsEnvironment.id
output apiName string = containerApp.name
output apiBaseUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
