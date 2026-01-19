/**
 * API Type Definitions
 * Matches the backend Pydantic models
 */

export interface AnalysisResponse {
  id: string
  summary: string
  next_actions: string[]
  created_at: string
  transcript: string
  observability?: ObservabilityMetadata
}

export interface ObservabilityMetadata {
  llm_provider: string
  llm_model: string
  input_tokens: number
  output_tokens: number
  latency_ms: number
}

export interface BatchAnalysisResponse {
  results: AnalysisResponse[]
  total: number
  successful: number
  failed: number
  errors?: string[]
}

export interface AnalysisEvaluation {
  id: string
  analysis_id: string
  score: number
  is_hallucination: boolean
  comment?: string
  evaluated_at: string
}

export interface AnalyticsResponse {
  total_analyses: number
  total_cost_usd: number
  cost_per_1000_requests: number
  total_input_tokens: number
  total_output_tokens: number
  avg_input_tokens: number
  avg_output_tokens: number
  avg_latency_ms: number
  p50_latency_ms: number
  p95_latency_ms: number
  p99_latency_ms: number
  total_evaluations: number
  avg_score?: number
  hallucination_rate?: number
  provider_breakdown: Record<string, number>
}

export interface HealthResponse {
  status: string
  checks?: Record<string, any>
}

export interface AnalyzeRequest {
  transcript: string
  num_next_actions?: number
}

export interface BatchAnalyzeRequest {
  transcripts: string[]
  num_next_actions?: number
}

export interface EvaluationRequest {
  score: number
  is_hallucination: boolean
  comment?: string
}
