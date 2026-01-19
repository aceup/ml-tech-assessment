'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { X, Clock, Zap, DollarSign, Activity, CheckCircle2, XCircle, Star, AlertTriangle, MessageSquare } from 'lucide-react'
import { useAnalysesQuery, useEvaluationsQuery } from '@/lib/queries'
import type { AnalysisResponse, AnalysisEvaluation } from '@/types/api'
import { useState } from 'react'

interface DetailedAnalyticsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function DetailedAnalyticsModal({
  isOpen,
  onClose,
}: DetailedAnalyticsModalProps) {
  const { data: analyses, isLoading: analysesLoading } = useAnalysesQuery()
  const { data: evaluations, isLoading: evaluationsLoading } = useEvaluationsQuery()
  const [expandedFeedback, setExpandedFeedback] = useState<string | null>(null)

  // Create a map of analysis_id -> evaluation for quick lookup
  const evaluationMap = new Map<string, AnalysisEvaluation>()
  evaluations?.forEach((evaluation) => {
    evaluationMap.set(evaluation.analysis_id, evaluation)
  })

  console.log('Evaluations:', evaluations)
  console.log('Evaluation Map:', Array.from(evaluationMap.entries()))

  const calculateCost = (analysis: AnalysisResponse) => {
    if (!analysis.observability) return 'N/A'
    const inputCost = (analysis.observability.input_tokens / 1_000_000) * 3.0
    const outputCost = (analysis.observability.output_tokens / 1_000_000) * 15.0
    return (inputCost + outputCost).toFixed(6)
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div
              className="glass-strong rounded-2xl border border-white/10 w-full max-w-6xl max-h-[90vh] overflow-hidden pointer-events-auto flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-slate-700/30">
                <div>
                  <h2 className="text-2xl font-bold text-slate-100">
                    Detailed Analytics
                  </h2>
                  <p className="text-sm text-slate-400 mt-1">
                    {analyses?.length || 0} total analyses
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-slate-800 transition-colors"
                  aria-label="Close modal"
                >
                  <X className="w-6 h-6 text-slate-400" />
                </button>
              </div>

              {/* Content */}
              <div className="overflow-auto flex-1 p-6">
                {analysesLoading || evaluationsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
                  </div>
                ) : !analyses || analyses.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-slate-400">No analyses available yet</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-slate-900/95 backdrop-blur z-10">
                        <tr className="border-b border-slate-700/30">
                          <th className="text-left p-3 text-slate-300 font-semibold">
                            Time
                          </th>
                          <th className="text-left p-3 text-slate-300 font-semibold">
                            Summary
                          </th>
                          <th className="text-right p-3 text-slate-300 font-semibold">
                            Latency
                          </th>
                          <th className="text-right p-3 text-slate-300 font-semibold">
                            Tokens
                          </th>
                          <th className="text-right p-3 text-slate-300 font-semibold">
                            Cost
                          </th>
                          <th className="text-right p-3 text-slate-300 font-semibold">
                            Actions
                          </th>
                          <th className="text-left p-3 text-slate-300 font-semibold">
                            Provider
                          </th>
                          <th className="text-center p-3 text-slate-300 font-semibold">
                            Feedback
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-700/30">
                        {analyses.map((analysis) => {
                          const timestamp = new Date(analysis.created_at)
                          const cost = calculateCost(analysis)
                          const evaluation = evaluationMap.get(analysis.id)

                          return (
                            <tr
                              key={analysis.id}
                              className="hover:bg-slate-800/30 transition-colors"
                            >
                              {/* Time */}
                              <td className="p-3 text-slate-300 whitespace-nowrap">
                                <div className="flex items-center gap-2">
                                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                                  <div>
                                    <div className="text-sm">
                                      {timestamp.toLocaleDateString('en-US', {
                                        month: 'short',
                                        day: 'numeric',
                                      })}
                                    </div>
                                    <div className="text-xs text-slate-500">
                                      {timestamp.toLocaleTimeString('en-US', {
                                        hour: '2-digit',
                                        minute: '2-digit',
                                      })}
                                    </div>
                                  </div>
                                </div>
                              </td>

                              {/* Summary */}
                              <td className="p-3 text-slate-300 max-w-md">
                                <div className="line-clamp-2" title={analysis.summary}>
                                  {analysis.summary}
                                </div>
                              </td>

                              {/* Latency */}
                              <td className="p-3 text-right">
                                {analysis.observability ? (
                                  <span
                                    className={`inline-flex items-center gap-1 ${
                                      analysis.observability.latency_ms < 1000
                                        ? 'text-green-400'
                                        : analysis.observability.latency_ms < 2000
                                        ? 'text-amber-400'
                                        : 'text-red-400'
                                    }`}
                                  >
                                    <Activity className="w-3.5 h-3.5" />
                                    {analysis.observability.latency_ms}ms
                                  </span>
                                ) : (
                                  <span className="text-slate-500">N/A</span>
                                )}
                              </td>

                              {/* Tokens */}
                              <td className="p-3 text-right">
                                {analysis.observability ? (
                                  <span className="inline-flex items-center gap-1 text-slate-300">
                                    <Zap className="w-3.5 h-3.5 text-purple-400" />
                                    {(
                                      analysis.observability.input_tokens +
                                      analysis.observability.output_tokens
                                    ).toLocaleString()}
                                  </span>
                                ) : (
                                  <span className="text-slate-500">N/A</span>
                                )}
                              </td>

                              {/* Cost */}
                              <td className="p-3 text-right">
                                {cost !== 'N/A' ? (
                                  <span className="inline-flex items-center gap-1 text-green-400">
                                    <DollarSign className="w-3.5 h-3.5" />
                                    ${cost}
                                  </span>
                                ) : (
                                  <span className="text-slate-500">N/A</span>
                                )}
                              </td>

                              {/* Actions */}
                              <td className="p-3 text-right text-slate-300">
                                {analysis.next_actions.length}
                              </td>

                              {/* Provider */}
                              <td className="p-3 text-slate-300">
                                <span className="inline-block px-2 py-1 rounded bg-slate-800/50 text-xs">
                                  {analysis.observability?.llm_provider || 'N/A'}
                                </span>
                              </td>

                              {/* Feedback */}
                              <td className="p-3">
                                {evaluation ? (
                                  <div className="flex flex-col items-start gap-2">
                                    {/* Stars */}
                                    <div className="flex items-center gap-1">
                                      {Array.from({ length: 5 }).map((_, i) => (
                                        <Star
                                          key={i}
                                          className={`w-3.5 h-3.5 ${
                                            i < evaluation.score
                                              ? 'fill-yellow-400 text-yellow-400'
                                              : 'text-slate-600'
                                          }`}
                                        />
                                      ))}
                                      <span className="text-xs text-slate-300 ml-1">
                                        ({evaluation.score}/5)
                                      </span>
                                    </div>

                                    {/* Hallucination Flag */}
                                    {evaluation.is_hallucination && (
                                      <div className="flex items-center gap-1 text-red-400">
                                        <AlertTriangle className="w-3.5 h-3.5" />
                                        <span className="text-xs font-medium">Hallucination</span>
                                      </div>
                                    )}

                                    {/* Comment */}
                                    {evaluation.comment && (
                                      <button
                                        onClick={() =>
                                          setExpandedFeedback(
                                            expandedFeedback === analysis.id ? null : analysis.id
                                          )
                                        }
                                        className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors"
                                      >
                                        <MessageSquare className="w-3.5 h-3.5" />
                                        <span className="text-xs">
                                          {expandedFeedback === analysis.id ? 'Hide' : 'Show'} comment
                                        </span>
                                      </button>
                                    )}

                                    {/* Expanded Comment */}
                                    {expandedFeedback === analysis.id && evaluation.comment && (
                                      <div className="mt-1 p-2 bg-slate-800/50 rounded text-xs text-slate-300 max-w-md">
                                        {evaluation.comment}
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <div className="flex items-center gap-1 text-slate-500">
                                    <XCircle className="w-3.5 h-3.5" />
                                    <span className="text-xs">No feedback</span>
                                  </div>
                                )}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between p-6 border-t border-slate-700/30">
                <p className="text-sm text-slate-400">
                  Showing all {analyses?.length || 0} analyses
                  {evaluations && evaluations.length > 0 && (
                    <span className="ml-2">
                      • {evaluations.length} with feedback
                    </span>
                  )}
                </p>
                <button
                  onClick={onClose}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
