'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Clock,
  Zap,
  DollarSign,
  Activity,
} from 'lucide-react'
import type { AnalysisResponse } from '@/types/api'

interface AnalysisCardProps {
  analysis: AnalysisResponse
  onFeedback?: (analysisId: string) => void
}

const priorityColors = {
  high: 'bg-red-500/20 text-red-300 border-red-500/30',
  medium: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  low: 'bg-green-500/20 text-green-300 border-green-500/30',
}

export default function AnalysisCard({ analysis, onFeedback }: AnalysisCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)

  const handleCopy = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedIndex(index)
      setTimeout(() => setCopiedIndex(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const getPriorityColor = (index: number) => {
    if (index === 0) return priorityColors.high
    if (index === 1) return priorityColors.medium
    return priorityColors.low
  }

  const calculateCost = (metadata: typeof analysis.observability) => {
    if (!metadata) return 0
    // Approximate cost calculation (Claude 3.5 Sonnet pricing)
    const inputCost = (metadata.input_tokens / 1_000_000) * 3.0
    const outputCost = (metadata.output_tokens / 1_000_000) * 15.0
    return (inputCost + outputCost).toFixed(6)
  }

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="glass rounded-2xl p-6 hover:shadow-xl transition-shadow duration-300"
      role="article"
      aria-label={`Analysis created at ${new Date(analysis.created_at).toLocaleString()}`}
    >
      {/* Header */}
      <header className="flex items-start justify-between gap-4 mb-4">
        <div className="flex-1">
          <time
            dateTime={analysis.created_at}
            className="text-sm text-slate-400 font-medium"
          >
            {new Date(analysis.created_at).toLocaleString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </time>
          <p className="text-xs text-slate-500 mt-1">ID: {analysis.id}</p>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="glass-strong rounded-lg p-2 hover:scale-105 transition-transform duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400"
          aria-expanded={isExpanded}
          aria-label={isExpanded ? 'Collapse summary' : 'Expand summary'}
        >
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-blue-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </button>
      </header>

      {/* Summary */}
      <section className="mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
          Summary
        </h3>
        <AnimatePresence mode="wait">
          {isExpanded ? (
            <motion.div
              key="expanded"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">
                {analysis.summary}
              </p>
            </motion.div>
          ) : (
            <motion.p
              key="collapsed"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="text-slate-300 line-clamp-2"
            >
              {analysis.summary}
            </motion.p>
          )}
        </AnimatePresence>
      </section>

      {/* Next Actions */}
      <section className="mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wide">
          Next Actions
        </h3>
        <ol className="space-y-3" role="list">
          {analysis.next_actions.map((action, index) => (
            <motion.li
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`glass-strong rounded-lg p-4 border transition-all duration-200 hover:border-white/20 ${getPriorityColor(
                index
              )}`}
              role="listitem"
            >
              <div className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-sm font-bold">
                  {index + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium leading-relaxed break-words">
                    {action}
                  </p>
                </div>
                <button
                  onClick={() => handleCopy(action, index)}
                  className="flex-shrink-0 p-2 rounded-lg hover:bg-white/10 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
                  aria-label={`Copy action: ${action}`}
                >
                  {copiedIndex === index ? (
                    <Check className="w-4 h-4" aria-label="Copied" />
                  ) : (
                    <Copy className="w-4 h-4 opacity-70" aria-hidden="true" />
                  )}
                </button>
              </div>
            </motion.li>
          ))}
        </ol>
      </section>

      {/* Observability Metadata */}
      {analysis.observability && (
        <motion.section
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-strong rounded-xl p-4 space-y-3"
          role="complementary"
          aria-label="Performance metrics"
        >
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Observability
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Latency */}
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-400" aria-hidden="true" />
              <div>
                <p className="text-xs text-slate-500">Latency</p>
                <p className="text-sm font-semibold text-slate-200">
                  {analysis.observability.latency_ms}ms
                </p>
              </div>
            </div>

            {/* Tokens */}
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-400" aria-hidden="true" />
              <div>
                <p className="text-xs text-slate-500">Tokens</p>
                <p className="text-sm font-semibold text-slate-200">
                  {analysis.observability.input_tokens + analysis.observability.output_tokens}
                </p>
              </div>
            </div>

            {/* Cost */}
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-green-400" aria-hidden="true" />
              <div>
                <p className="text-xs text-slate-500">Cost</p>
                <p className="text-sm font-semibold text-slate-200">
                  ${calculateCost(analysis.observability)}
                </p>
              </div>
            </div>

            {/* Model */}
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-orange-400" aria-hidden="true" />
              <div>
                <p className="text-xs text-slate-500">Model</p>
                <p className="text-sm font-semibold text-slate-200 truncate">
                  {analysis.observability.llm_model}
                </p>
              </div>
            </div>
          </div>
        </motion.section>
      )}

      {/* Feedback Button */}
      {onFeedback && (
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-6 pt-4 border-t border-slate-700"
        >
          <button
            onClick={() => onFeedback(analysis.id)}
            className="w-full glass-strong rounded-lg py-2.5 px-4 text-sm font-medium text-slate-300 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400"
            aria-label="Provide feedback for this analysis"
          >
            Provide Feedback
          </button>
        </motion.footer>
      )}
    </motion.article>
  )
}
