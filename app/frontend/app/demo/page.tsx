'use client'

import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  AnalysisCard,
  TranscriptInput,
  BatchAnalyzer,
  FeedbackModal,
  useToast,
} from '@/components'
import { ToastContainer } from '@/components/Toast'
import { apiClient } from '@/lib/api-client'
import type { AnalysisResponse } from '@/types/api'

const queryClient = new QueryClient()

function DemoContent() {
  const [transcript, setTranscript] = useState('')
  const [analyses, setAnalyses] = useState<AnalysisResponse[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('single')
  const { toasts, addToast } = useToast()

  const handleAnalyze = async () => {
    if (transcript.trim().length < 10) {
      addToast('Transcript must be at least 10 characters', 'error')
      return
    }

    setIsAnalyzing(true)
    try {
      const result = await apiClient.analyzeTranscript(transcript)
      setAnalyses([result, ...analyses])
      setTranscript('')
      addToast('Analysis completed successfully!', 'success')
    } catch (error) {
      addToast(
        error instanceof Error ? error.message : 'Analysis failed',
        'error'
      )
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleBatchAnalyze = async (transcripts: string[]) => {
    try {
      const result = await apiClient.batchAnalyze(transcripts)
      setAnalyses([...result.results, ...analyses])
      addToast(
        `Batch analysis completed: ${result.successful} successful, ${result.failed} failed`,
        result.failed > 0 ? 'info' : 'success'
      )
      return result
    } catch (error) {
      addToast(
        error instanceof Error ? error.message : 'Batch analysis failed',
        'error'
      )
      throw error
    }
  }

  const handleFeedback = async (feedback: any) => {
    if (!selectedAnalysisId) return

    try {
      await apiClient.submitFeedback(selectedAnalysisId, feedback)
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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="glass-strong border-b border-slate-800 sticky top-0 z-30 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold gradient-text">
            ML Tech Assessment - Component Demo
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Premium glassmorphic UI components showcase
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-8">
          <button
            onClick={() => setActiveTab('single')}
            className={`glass-strong rounded-lg px-6 py-2.5 text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 ${
              activeTab === 'single'
                ? 'bg-blue-500/20 text-blue-300'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Single Analysis
          </button>
          <button
            onClick={() => setActiveTab('batch')}
            className={`glass-strong rounded-lg px-6 py-2.5 text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 ${
              activeTab === 'batch'
                ? 'bg-blue-500/20 text-blue-300'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Batch Analysis
          </button>
        </div>

        {/* Content */}
        {activeTab === 'single' ? (
          <div className="space-y-8">
            {/* Input Section */}
            <section className="glass rounded-2xl p-6">
              <TranscriptInput
                value={transcript}
                onChange={setTranscript}
                isLoading={isAnalyzing}
                placeholder="Enter a medical consultation transcript to analyze..."
                label="Medical Transcript"
                maxLength={5000}
              />
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing || transcript.trim().length < 10}
                className="mt-4 w-full glass-strong rounded-lg py-3 px-6 text-sm font-medium bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze Transcript'}
              </button>
            </section>

            {/* Results Section */}
            {analyses.length > 0 && (
              <section>
                <h2 className="text-xl font-bold text-slate-200 mb-4">
                  Recent Analyses
                </h2>
                <div className="space-y-4">
                  {analyses.map((analysis) => (
                    <AnalysisCard
                      key={analysis.id}
                      analysis={analysis}
                      onFeedback={(id) => setSelectedAnalysisId(id)}
                    />
                  ))}
                </div>
              </section>
            )}
          </div>
        ) : (
          <section className="glass rounded-2xl p-6">
            <BatchAnalyzer
              onAnalyze={handleBatchAnalyze}
              maxTranscripts={5}
              minTranscriptLength={10}
            />
          </section>
        )}
      </main>

      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={selectedAnalysisId !== null}
        onClose={() => setSelectedAnalysisId(null)}
        onSubmit={handleFeedback}
        analysisId={selectedAnalysisId || ''}
      />

      {/* Toast Container */}
      <ToastContainer
        toasts={toasts}
        onClose={(id) => {
          // Remove toast with matching id
        }}
      />
    </div>
  )
}

export default function DemoPage() {
  return (
    <QueryClientProvider client={queryClient}>
      <DemoContent />
    </QueryClientProvider>
  )
}
