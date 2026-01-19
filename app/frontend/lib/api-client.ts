/**
 * API Client
 * Handles all API communication with the backend
 */

import { getApiUrl, getApiHeaders } from './config'
import type {
  AnalysisResponse,
  BatchAnalysisResponse,
  AnalyticsResponse,
  HealthResponse,
  EvaluationRequest,
  AnalysisEvaluation,
} from '@/types/api'

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function fetchApi<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = getApiUrl(path)
  const headers = {
    ...getApiHeaders(),
    ...options.headers,
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.detail || `HTTP ${response.status}`,
        response.status,
        errorData
      )
    }

    return response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Network error',
      0
    )
  }
}

export const apiClient = {
  // Health endpoints
  async checkHealth(): Promise<HealthResponse> {
    return fetchApi<HealthResponse>('/health/live')
  },

  async checkReadiness(): Promise<HealthResponse> {
    return fetchApi<HealthResponse>('/health/ready')
  },

  // Analysis endpoints
  async analyzeTranscript(
    transcript: string,
    numNextActions: number = 3
  ): Promise<AnalysisResponse> {
    const params = new URLSearchParams({
      transcript,
      num_next_actions: numNextActions.toString(),
    })
    return fetchApi<AnalysisResponse>(`/analyses/analyze?${params}`)
  },

  async batchAnalyze(
    transcripts: string[],
    numNextActions: number = 3
  ): Promise<BatchAnalysisResponse> {
    return fetchApi<BatchAnalysisResponse>('/analyses/batch', {
      method: 'POST',
      body: JSON.stringify({
        transcripts,
        num_next_actions: numNextActions,
      }),
    })
  },

  async getAnalysis(analysisId: string): Promise<AnalysisResponse> {
    return fetchApi<AnalysisResponse>(`/analyses/${analysisId}`)
  },

  async listAnalyses(): Promise<AnalysisResponse[]> {
    return fetchApi<AnalysisResponse[]>('/analyses')
  },

  async submitFeedback(
    analysisId: string,
    feedback: EvaluationRequest
  ): Promise<AnalysisEvaluation> {
    return fetchApi<AnalysisEvaluation>(`/analyses/${analysisId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    })
  },

  async listEvaluations(): Promise<AnalysisEvaluation[]> {
    return fetchApi<AnalysisEvaluation[]>('/analyses/evaluations')
  },

  // Analytics endpoints
  async getMetrics(): Promise<AnalyticsResponse> {
    return fetchApi<AnalyticsResponse>('/analytics/metrics')
  },
}
