'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Star, AlertTriangle, Send, Loader2 } from 'lucide-react'
import type { EvaluationRequest } from '@/types/api'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (feedback: EvaluationRequest) => Promise<void>
  analysisId: string
}

export default function FeedbackModal({
  isOpen,
  onClose,
  analysisId,
  onSubmit,
}: FeedbackModalProps) {
  const [rating, setRating] = useState(0)
  const [hoveredRating, setHoveredRating] = useState(0)
  const [isHallucination, setIsHallucination] = useState(false)
  const [comment, setComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (rating === 0) {
      setError('Please provide a rating')
      return
    }

    setIsSubmitting(true)

    try {
      await onSubmit({
        score: rating,
        is_hallucination: isHallucination,
        comment: comment.trim() || undefined,
      })
      handleClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      setRating(0)
      setHoveredRating(0)
      setIsHallucination(false)
      setComment('')
      setError(null)
      onClose()
    }
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
            onClick={handleClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            aria-hidden="true"
          />

          {/* Modal */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className="glass-strong rounded-2xl p-6 w-full max-w-md shadow-2xl"
              role="dialog"
              aria-labelledby="feedback-modal-title"
              aria-describedby="feedback-modal-description"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <header className="flex items-center justify-between mb-6">
                <div>
                  <h2
                    id="feedback-modal-title"
                    className="text-xl font-bold text-slate-200"
                  >
                    Provide Feedback
                  </h2>
                  <p
                    id="feedback-modal-description"
                    className="text-sm text-slate-400 mt-1"
                  >
                    Help us improve analysis quality
                  </p>
                </div>
                <button
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="glass rounded-lg p-2 hover:bg-slate-700/50 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Close modal"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </header>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Star Rating */}
                <div>
                  <label className="block text-sm font-semibold text-slate-300 mb-3">
                    Rating <span className="text-red-400">*</span>
                  </label>
                  <div
                    className="flex gap-2 justify-center"
                    role="radiogroup"
                    aria-label="Rating"
                    aria-required="true"
                  >
                    {[1, 2, 3, 4, 5].map((star) => (
                      <motion.button
                        key={star}
                        type="button"
                        onClick={() => setRating(star)}
                        onMouseEnter={() => setHoveredRating(star)}
                        onMouseLeave={() => setHoveredRating(0)}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.95 }}
                        className="focus:outline-none focus:ring-2 focus:ring-blue-400 rounded-lg p-1"
                        aria-label={`${star} star${star !== 1 ? 's' : ''}`}
                        role="radio"
                        aria-checked={rating === star}
                      >
                        <Star
                          className={`w-8 h-8 transition-all duration-200 ${
                            star <= (hoveredRating || rating)
                              ? 'fill-yellow-400 text-yellow-400'
                              : 'text-slate-600'
                          }`}
                        />
                      </motion.button>
                    ))}
                  </div>
                  {rating > 0 && (
                    <p className="text-center text-sm text-slate-400 mt-2">
                      {rating === 1 && 'Poor'}
                      {rating === 2 && 'Fair'}
                      {rating === 3 && 'Good'}
                      {rating === 4 && 'Very Good'}
                      {rating === 5 && 'Excellent'}
                    </p>
                  )}
                </div>

                {/* Hallucination Toggle */}
                <div className="glass rounded-xl p-4">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isHallucination}
                      onChange={(e) => setIsHallucination(e.target.checked)}
                      disabled={isSubmitting}
                      className="mt-1 w-5 h-5 rounded border-slate-600 bg-slate-800 text-orange-500 focus:ring-2 focus:ring-orange-400 transition-colors duration-200"
                      aria-describedby="hallucination-description"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-orange-400" />
                        <span className="font-semibold text-slate-200 text-sm">
                          Report Hallucination
                        </span>
                      </div>
                      <p
                        id="hallucination-description"
                        className="text-xs text-slate-400 mt-1"
                      >
                        Check if the analysis contains incorrect or fabricated information
                      </p>
                    </div>
                  </label>
                </div>

                {/* Comment */}
                <div>
                  <label
                    htmlFor="feedback-comment"
                    className="block text-sm font-semibold text-slate-300 mb-2"
                  >
                    Additional Comments (Optional)
                  </label>
                  <textarea
                    id="feedback-comment"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    disabled={isSubmitting}
                    placeholder="Share your thoughts..."
                    className="w-full glass rounded-xl px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none min-h-[100px] disabled:opacity-50"
                    maxLength={500}
                  />
                  <p className="text-xs text-slate-500 mt-1 text-right">
                    {comment.length} / 500
                  </p>
                </div>

                {/* Error Message */}
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-strong rounded-lg p-3 border border-red-500/30"
                    role="alert"
                  >
                    <p className="text-sm text-red-400 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      {error}
                    </p>
                  </motion.div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={handleClose}
                    disabled={isSubmitting}
                    className="flex-1 glass rounded-lg py-2.5 px-4 text-sm font-medium text-slate-300 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || rating === 0}
                    className="flex-1 glass-strong rounded-lg py-2.5 px-4 text-sm font-medium bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        Submit Feedback
                      </>
                    )}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  )
}
