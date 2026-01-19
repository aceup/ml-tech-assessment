/**
 * TanStack Query hooks
 * React Query hooks for API data fetching
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './api-client'
import type { EvaluationRequest } from '@/types/api'

// Query keys
export const queryKeys = {
  health: ['health'] as const,
  analyses: ['analyses'] as const,
  analysis: (id: string) => ['analysis', id] as const,
  analytics: ['analytics'] as const,
}

// Health queries
export function useHealthQuery() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => apiClient.checkHealth(),
    refetchInterval: 30000, // Refetch every 30s
    retry: 3,
  })
}

// Analysis queries
export function useAnalysesQuery() {
  return useQuery({
    queryKey: queryKeys.analyses,
    queryFn: () => apiClient.listAnalyses(),
    staleTime: 10000, // Consider data fresh for 10s
  })
}

export function useAnalysisQuery(analysisId: string) {
  return useQuery({
    queryKey: queryKeys.analysis(analysisId),
    queryFn: () => apiClient.getAnalysis(analysisId),
    enabled: !!analysisId,
  })
}

// Analytics query
export function useAnalyticsQuery() {
  return useQuery({
    queryKey: queryKeys.analytics,
    queryFn: () => apiClient.getMetrics(),
    staleTime: 30000, // Consider data fresh for 30s
  })
}

// Evaluations query
export function useEvaluationsQuery() {
  return useQuery({
    queryKey: ['evaluations'],
    queryFn: () => apiClient.listEvaluations(),
    staleTime: 30000, // Consider data fresh for 30s
  })
}

// Mutations
export function useAnalyzeMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      transcript,
      numNextActions = 3,
    }: {
      transcript: string
      numNextActions?: number
    }) => apiClient.analyzeTranscript(transcript, numNextActions),
    onSuccess: () => {
      // Invalidate analyses list to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.analyses })
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics })
    },
  })
}

export function useBatchAnalyzeMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      transcripts,
      numNextActions = 3,
    }: {
      transcripts: string[]
      numNextActions?: number
    }) => apiClient.batchAnalyze(transcripts, numNextActions),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.analyses })
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics })
    },
  })
}

export function useSubmitFeedbackMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      analysisId,
      feedback,
    }: {
      analysisId: string
      feedback: EvaluationRequest
    }) => apiClient.submitFeedback(analysisId, feedback),
    onSuccess: (_, variables) => {
      // Invalidate the specific analysis and analytics
      queryClient.invalidateQueries({
        queryKey: queryKeys.analysis(variables.analysisId),
      })
      queryClient.invalidateQueries({ queryKey: queryKeys.analytics })
    },
  })
}
