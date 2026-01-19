/**
 * Application configuration
 * Handles environment variables and API settings
 */

export const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    apiKey: process.env.NEXT_PUBLIC_API_KEY || '',
    version: 'v1',
  },
  app: {
    name: 'Medical Transcript Analyzer',
    description: 'AI-powered medical transcript analysis with real-time insights',
  },
} as const

/**
 * Get full API endpoint URL
 */
export function getApiUrl(path: string): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${config.api.baseUrl}/api/${config.api.version}${cleanPath}`
}

/**
 * Get API headers with authentication
 */
export function getApiHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'X-API-Key': config.api.apiKey,
  }
}
