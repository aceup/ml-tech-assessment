'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus,
  Trash2,
  Play,
  CheckCircle2,
  XCircle,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import type { BatchAnalysisResponse } from '@/types/api'

interface BatchAnalyzerProps {
  onAnalyze: (transcripts: string[]) => Promise<BatchAnalysisResponse>
  maxTranscripts?: number
  minTranscriptLength?: number
}

interface TranscriptItem {
  id: string
  text: string
  status: 'idle' | 'processing' | 'success' | 'error'
  error?: string
}

export default function BatchAnalyzer({
  onAnalyze,
  maxTranscripts = 10,
  minTranscriptLength = 10,
}: BatchAnalyzerProps) {
  const [transcripts, setTranscripts] = useState<TranscriptItem[]>([
    { id: crypto.randomUUID(), text: '', status: 'idle' },
  ])
  const [isProcessing, setIsProcessing] = useState(false)
  const [results, setResults] = useState<BatchAnalysisResponse | null>(null)

  const addTranscript = () => {
    if (transcripts.length < maxTranscripts) {
      setTranscripts([
        ...transcripts,
        { id: crypto.randomUUID(), text: '', status: 'idle' },
      ])
    }
  }

  const removeTranscript = (id: string) => {
    if (transcripts.length > 1) {
      setTranscripts(transcripts.filter((t) => t.id !== id))
    }
  }

  const updateTranscript = (id: string, text: string) => {
    setTranscripts(
      transcripts.map((t) => (t.id === id ? { ...t, text } : t))
    )
  }

  const handleAnalyze = async () => {
    // Validate transcripts
    const validTranscripts = transcripts.filter(
      (t) => t.text.trim().length >= minTranscriptLength
    )

    if (validTranscripts.length === 0) {
      return
    }

    setIsProcessing(true)
    setResults(null)

    // Update status to processing
    setTranscripts(
      transcripts.map((t) => ({
        ...t,
        status: t.text.trim().length >= minTranscriptLength ? 'processing' : 'idle',
      }))
    )

    try {
      const response = await onAnalyze(validTranscripts.map((t) => t.text.trim()))
      setResults(response)

      // Update status based on results
      setTranscripts(
        transcripts.map((t) => {
          if (t.text.trim().length < minTranscriptLength) {
            return t
          }
          const wasSuccessful = response.successful > 0
          return {
            ...t,
            status: wasSuccessful ? 'success' : 'error',
            error: !wasSuccessful ? 'Analysis failed' : undefined,
          }
        })
      )
    } catch (error) {
      // Update all to error status
      setTranscripts(
        transcripts.map((t) => ({
          ...t,
          status: t.text.trim().length >= minTranscriptLength ? 'error' : 'idle',
          error: error instanceof Error ? error.message : 'Analysis failed',
        }))
      )
    } finally {
      setIsProcessing(false)
    }
  }

  const validCount = transcripts.filter(
    (t) => t.text.trim().length >= minTranscriptLength
  ).length

  const getStatusIcon = (status: TranscriptItem['status']) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />
      case 'error':
        return <XCircle className="w-4 h-4 text-red-400" />
      default:
        return null
    }
  }

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-200">Batch Analysis</h2>
          <p className="text-sm text-slate-400 mt-1">
            Analyze up to {maxTranscripts} transcripts simultaneously
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">
            {validCount} / {transcripts.length} valid
          </span>
        </div>
      </div>

      {/* Transcript Inputs */}
      <div className="space-y-3">
        <AnimatePresence mode="popLayout">
          {transcripts.map((transcript, index) => (
            <motion.div
              key={transcript.id}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ duration: 0.2 }}
              className="glass rounded-xl p-4"
            >
              <div className="flex items-start gap-3">
                {/* Index */}
                <div className="flex-shrink-0 w-8 h-8 glass-strong rounded-lg flex items-center justify-center text-sm font-semibold text-slate-300">
                  {index + 1}
                </div>

                {/* Textarea */}
                <textarea
                  value={transcript.text}
                  onChange={(e) => updateTranscript(transcript.id, e.target.value)}
                  placeholder={`Transcript ${index + 1}...`}
                  disabled={isProcessing}
                  className="flex-1 bg-transparent text-slate-200 placeholder-slate-500 focus:outline-none resize-none min-h-[80px] disabled:opacity-50"
                  aria-label={`Transcript ${index + 1}`}
                />

                {/* Status Icon */}
                <div className="flex-shrink-0 w-8 flex items-center justify-center">
                  {getStatusIcon(transcript.status)}
                </div>

                {/* Delete Button */}
                {transcripts.length > 1 && (
                  <button
                    onClick={() => removeTranscript(transcript.id)}
                    disabled={isProcessing}
                    className="flex-shrink-0 glass-strong rounded-lg p-2 hover:bg-red-500/20 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-red-400 disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label={`Remove transcript ${index + 1}`}
                  >
                    <Trash2 className="w-4 h-4 text-slate-400" />
                  </button>
                )}
              </div>

              {/* Error Message */}
              {transcript.error && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-2 text-sm text-red-400 flex items-center gap-2"
                  role="alert"
                >
                  <AlertCircle className="w-4 h-4" />
                  {transcript.error}
                </motion.p>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <button
          onClick={addTranscript}
          disabled={transcripts.length >= maxTranscripts || isProcessing}
          className="glass-strong rounded-lg px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          aria-label="Add transcript"
        >
          <Plus className="w-4 h-4" />
          Add Transcript
        </button>

        <button
          onClick={handleAnalyze}
          disabled={validCount === 0 || isProcessing}
          className="glass-strong rounded-lg px-6 py-2 text-sm font-medium bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          aria-label="Analyze all transcripts"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Analyze All
            </>
          )}
        </button>
      </div>

      {/* Results Summary */}
      {results && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-strong rounded-xl p-6 space-y-4"
          role="status"
          aria-live="polite"
        >
          <h3 className="text-lg font-semibold text-slate-200">Results</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-400">{results.total}</p>
              <p className="text-sm text-slate-400">Total</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-400">{results.successful}</p>
              <p className="text-sm text-slate-400">Successful</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-400">{results.failed}</p>
              <p className="text-sm text-slate-400">Failed</p>
            </div>
          </div>

          {results.errors && results.errors.length > 0 && (
            <div className="pt-4 border-t border-slate-700">
              <p className="text-sm font-semibold text-slate-300 mb-2">Errors:</p>
              <ul className="space-y-1" role="list">
                {results.errors.map((error, index) => (
                  <li key={index} className="text-sm text-red-400 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <span>{error}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
