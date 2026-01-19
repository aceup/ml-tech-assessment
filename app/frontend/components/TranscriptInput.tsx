'use client'

import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Clipboard, Loader2 } from 'lucide-react'

interface TranscriptInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  minHeight?: number
  maxHeight?: number
  maxLength?: number
  isLoading?: boolean
  error?: string
  id?: string
  label?: string
}

export default function TranscriptInput({
  value,
  onChange,
  placeholder = 'Enter transcript...',
  minHeight = 120,
  maxHeight = 400,
  maxLength = 10000,
  isLoading = false,
  error,
  id = 'transcript-input',
  label = 'Transcript',
}: TranscriptInputProps) {
  const [isPasteShimmering, setIsPasteShimmering] = useState(false)
  const [height, setHeight] = useState(minHeight)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      const scrollHeight = textareaRef.current.scrollHeight
      const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight)
      setHeight(newHeight)
    }
  }, [value, minHeight, maxHeight])

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText()
      if (text) {
        const truncatedText = text.slice(0, maxLength)
        onChange(truncatedText)
        setIsPasteShimmering(true)
        setTimeout(() => setIsPasteShimmering(false), 1000)
      }
    } catch (err) {
      console.error('Failed to read clipboard:', err)
    }
  }

  const characterCount = value.length
  const isNearLimit = characterCount > maxLength * 0.9
  const isAtLimit = characterCount >= maxLength

  return (
    <div className="w-full">
      {/* Label */}
      <div className="flex items-center justify-between mb-2">
        <label
          htmlFor={id}
          className="text-sm font-semibold text-slate-300 uppercase tracking-wide"
        >
          {label}
        </label>
        <div className="flex items-center gap-3">
          {/* Character Count */}
          <span
            className={`text-xs font-medium transition-colors duration-200 ${
              isAtLimit
                ? 'text-red-400'
                : isNearLimit
                ? 'text-yellow-400'
                : 'text-slate-500'
            }`}
            aria-live="polite"
            aria-atomic="true"
          >
            {characterCount.toLocaleString()} / {maxLength.toLocaleString()}
          </span>

          {/* Paste Button */}
          <button
            onClick={handlePaste}
            disabled={isLoading}
            className="glass-strong rounded-lg p-2 hover:scale-105 transition-transform duration-200 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Paste from clipboard"
            title="Paste from clipboard"
          >
            <Clipboard className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Textarea Container */}
      <div className="relative">
        {/* Shimmer Effect */}
        {isPasteShimmering && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 shimmer rounded-xl pointer-events-none z-10"
            aria-hidden="true"
          />
        )}

        {/* Loading Skeleton */}
        {isLoading ? (
          <div className="glass rounded-xl p-4 flex items-center justify-center" style={{ height }}>
            <Loader2 className="w-6 h-6 text-blue-400 animate-spin" aria-label="Loading" />
          </div>
        ) : (
          <>
            {/* Textarea */}
            <textarea
              ref={textareaRef}
              id={id}
              value={value}
              onChange={(e) => {
                const newValue = e.target.value.slice(0, maxLength)
                onChange(newValue)
              }}
              placeholder={placeholder}
              disabled={isLoading}
              className={`w-full glass rounded-xl px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 transition-all duration-200 resize-none ${
                error
                  ? 'ring-2 ring-red-500 focus:ring-red-400'
                  : 'focus:ring-blue-400'
              }`}
              style={{ height: `${height}px` }}
              aria-invalid={!!error}
              aria-describedby={error ? `${id}-error` : undefined}
              spellCheck="true"
            />

            {/* Error Message */}
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                id={`${id}-error`}
                className="mt-2 text-sm text-red-400 flex items-center gap-2"
                role="alert"
              >
                <span className="w-1 h-1 rounded-full bg-red-400" />
                {error}
              </motion.p>
            )}
          </>
        )}
      </div>

      {/* Help Text */}
      {!error && (
        <p className="mt-2 text-xs text-slate-500" id={`${id}-help`}>
          Paste or type the transcript you want to analyze. The text will auto-expand as you type.
        </p>
      )}
    </div>
  )
}
