'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, BarChart3, History } from 'lucide-react'
import TranscriptInput from '@/components/TranscriptInput'
import AnalysisCard from '@/components/AnalysisCard'
import AnalyticsDashboard from '@/components/AnalyticsDashboard'
import { AnalysisHistory } from '@/components/AnalysisHistory'
import { ToastContainer } from '@/components/Toast'
import FeedbackModal from '@/components/FeedbackModal'
import { useToast } from '@/components/hooks'
import { useAnalyzeMutation } from '@/lib/queries'
import { apiClient } from '@/lib/api-client'
import type { AnalysisResponse, EvaluationRequest } from '@/types/api'

export default function Home() {
  const [transcript, setTranscript] = useState('')
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResponse | null>(null)
  const [showAnalytics, setShowAnalytics] = useState(false)
  const [numNextActions, setNumNextActions] = useState(3)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [feedbackAnalysisId, setFeedbackAnalysisId] = useState<string | null>(null)
  const { toasts, addToast } = useToast()

  const analyzeMutation = useAnalyzeMutation()

  const handleAnalyze = async () => {
    if (transcript.trim().length < 10) {
      addToast('Transcript must be at least 10 characters', 'error')
      return
    }

    try {
      const result = await analyzeMutation.mutateAsync({
        transcript: transcript.trim(),
        numNextActions,
      })
      setCurrentAnalysis(result)
      setTranscript('')
      addToast('Analysis completed successfully!', 'success')
    } catch (error) {
      addToast(
        error instanceof Error ? error.message : 'Analysis failed',
        'error'
      )
    }
  }

  const handleOpenFeedback = (analysisId: string) => {
    setFeedbackAnalysisId(analysisId)
    setShowFeedbackModal(true)
  }

  const handleSubmitFeedback = async (feedback: EvaluationRequest) => {
    if (!feedbackAnalysisId) return

    try {
      await apiClient.submitFeedback(feedbackAnalysisId, feedback)
      addToast('Feedback submitted successfully!', 'success')
    } catch (error) {
      addToast(
        error instanceof Error ? error.message : 'Failed to submit feedback',
        'error'
      )
      throw error
    }
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold gradient-text font-[family-name:var(--font-playfair)]">
                Coaching Transcript Analyzer
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                AI-powered analysis with real-time insights
              </p>
            </div>
            <button
              onClick={() => setShowAnalytics(!showAnalytics)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                showAnalytics
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'glass hover:bg-slate-800/50 text-slate-300'
              }`}
            >
              {showAnalytics ? (
                <>
                  <Activity className="w-4 h-4" />
                  Hide Analytics
                </>
              ) : (
                <>
                  <BarChart3 className="w-4 h-4" />
                  Show Analytics
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content - Three-Zone Layout */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Zone 1: Input Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-8 space-y-6"
          >
            {/* Input Card */}
            <div className="glass-strong rounded-2xl p-6 border border-slate-700/50">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-slate-100">
                    Analyze Transcript
                  </h2>
                  <p className="text-sm text-slate-400">
                    Enter medical transcript for AI analysis
                  </p>
                </div>
              </div>

              <TranscriptInput
                value={transcript}
                onChange={setTranscript}
                placeholder="Paste or type medical transcript here..."
                isLoading={analyzeMutation.isPending}
                minHeight={200}
                maxHeight={400}
              />

              <div className="mt-6 space-y-4">
                {/* Number of Next Actions Control */}
                <div className="flex items-center gap-4">
                  <label htmlFor="numNextActions" className="text-sm text-slate-400 font-medium">
                    Number of next actions:
                  </label>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setNumNextActions(Math.max(1, numNextActions - 1))}
                      disabled={analyzeMutation.isPending || numNextActions <= 1}
                      className="glass-strong rounded-lg p-2 hover:bg-slate-700/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-400"
                      aria-label="Decrease number of actions"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                      </svg>
                    </button>
                    <input
                      id="numNextActions"
                      type="number"
                      min="1"
                      max="10"
                      value={numNextActions}
                      onChange={(e) => setNumNextActions(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
                      disabled={analyzeMutation.isPending}
                      className="w-16 glass-strong rounded-lg px-3 py-2 text-center text-slate-200 font-semibold focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50"
                    />
                    <button
                      type="button"
                      onClick={() => setNumNextActions(Math.min(10, numNextActions + 1))}
                      disabled={analyzeMutation.isPending || numNextActions >= 10}
                      className="glass-strong rounded-lg p-2 hover:bg-slate-700/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-400"
                      aria-label="Increase number of actions"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                    </button>
                  </div>
                  <span className="text-xs text-slate-500">(1-10)</span>
                </div>

                {/* Analyze Button Row */}
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-400">
                    Analysis includes summary and recommended next actions
                  </p>
                  <button
                    onClick={handleAnalyze}
                    disabled={analyzeMutation.isPending || transcript.trim().length < 10}
                    className={`px-6 py-3 rounded-lg font-medium transition-all ${
                      analyzeMutation.isPending || transcript.trim().length < 10
                        ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:shadow-lg hover:shadow-purple-500/20 hover:scale-105'
                    }`}
                  >
                    {analyzeMutation.isPending ? (
                      <span className="flex items-center gap-2">
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Analyzing...
                      </span>
                    ) : (
                      'Analyze Transcript'
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Results Section */}
            {currentAnalysis && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                <AnalysisCard
                  analysis={currentAnalysis}
                  onFeedback={handleOpenFeedback}
                />
              </motion.div>
            )}

            {!currentAnalysis && !analyzeMutation.isPending && (
              <div className="glass rounded-2xl p-12 text-center border border-slate-700/50">
                <div className="w-16 h-16 rounded-full bg-slate-800/50 mx-auto mb-4 flex items-center justify-center">
                  <Activity className="w-8 h-8 text-slate-500" />
                </div>
                <h3 className="text-lg font-medium text-slate-300 mb-2">
                  No Analysis Yet
                </h3>
                <p className="text-slate-400 text-sm">
                  Enter a transcript above and click "Analyze" to get started
                </p>
              </div>
            )}
          </motion.div>

          {/* Zone 2 & 3: Analytics & History Sidebar */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="lg:col-span-4 space-y-6"
          >
            {/* Analytics Toggle Section */}
            {showAnalytics ? (
              <div className="glass-strong rounded-2xl p-6 border border-slate-700/50">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-slate-100">
                      Analytics
                    </h2>
                    <p className="text-xs text-slate-400">
                      Real-time metrics
                    </p>
                  </div>
                </div>
                <AnalyticsDashboard />
              </div>
            ) : (
              <div className="glass-strong rounded-2xl p-6 border border-slate-700/50">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                    <History className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-slate-100">
                      History
                    </h2>
                    <p className="text-xs text-slate-400">
                      Past analyses
                    </p>
                  </div>
                </div>
                <AnalysisHistory
                  onAnalysisSelect={(analysis) => {
                    setCurrentAnalysis(analysis)
                    addToast('Analysis loaded from history', 'info')
                  }}
                  maxHeight="calc(100vh - 300px)"
                />
              </div>
            )}
          </motion.div>
        </div>
      </main>

      {/* Toast Container */}
      <ToastContainer toasts={toasts} onClose={() => {}} />

      {/* Feedback Modal */}
      {feedbackAnalysisId && (
        <FeedbackModal
          isOpen={showFeedbackModal}
          onClose={() => setShowFeedbackModal(false)}
          analysisId={feedbackAnalysisId}
          onSubmit={handleSubmitFeedback}
        />
      )}
    </div>
  )
}
