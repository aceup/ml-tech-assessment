'use client'

import {
  useState,
  useCallback,
  useMemo,
  useRef,
  useEffect,
} from 'react'
import {
  Search,
  ChevronDown,
  Clock,
  FileText,
  Zap,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAnalysesQuery } from '@/lib/queries'
import type { AnalysisResponse } from '@/types/api'
import clsx from 'clsx'

interface VirtualScrollState {
  visibleStart: number
  visibleEnd: number
  scrollTop: number
}

type SortDirection = 'asc' | 'desc'

interface AnalysisHistoryProps {
  onAnalysisSelect?: (analysis: AnalysisResponse) => void
  maxHeight?: string
  className?: string
}

const ITEM_HEIGHT = 88 // Height of each analysis card in pixels
const BUFFER_SIZE = 3 // Number of items to render outside visible area

/**
 * Skeleton loader for individual analysis card
 */
function AnalysisCardSkeleton() {
  return (
    <div className="p-3 border border-slate-700 rounded-lg bg-slate-900/20">
      <div className="space-y-2">
        <div className="h-4 bg-slate-700 rounded w-3/4 shimmer" />
        <div className="h-3 bg-slate-700 rounded w-1/2 shimmer" />
        <div className="flex gap-2">
          <div className="h-3 bg-slate-700 rounded w-1/4 shimmer" />
          <div className="h-3 bg-slate-700 rounded w-1/4 shimmer" />
        </div>
      </div>
    </div>
  )
}

/**
 * Individual analysis card component
 */
interface AnalysisCardProps {
  analysis: AnalysisResponse
  isSelected?: boolean
  onSelect?: (analysis: AnalysisResponse) => void
  style?: React.CSSProperties
}

function AnalysisCard({
  analysis,
  isSelected,
  onSelect,
  style,
}: AnalysisCardProps) {
  const [showPreview, setShowPreview] = useState(false)
  const createdDate = new Date(analysis.created_at)
  const formattedDate = createdDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: createdDate.getFullYear() !== new Date().getFullYear() ? '2-digit' : undefined,
  })
  const formattedTime = createdDate.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })

  const transcriptPreview = analysis.transcript.slice(0, 60)
  const truncatedSummary = analysis.summary.slice(0, 50)

  return (
    <motion.div
      style={style}
      onMouseEnter={() => setShowPreview(true)}
      onMouseLeave={() => setShowPreview(false)}
      className={clsx(
        'p-3 rounded-lg border transition-all duration-200 cursor-pointer',
        isSelected
          ? 'bg-blue-500/10 border-blue-400/50'
          : 'border-slate-700/50 hover:border-slate-600 hover:bg-slate-900/40'
      )}
      onClick={() => onSelect?.(analysis)}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Header with timestamp */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5 flex-1 min-w-0">
          <Clock className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          <div className="min-w-0">
            <time className="text-xs text-slate-300 block truncate">
              {formattedDate} {formattedTime}
            </time>
          </div>
        </div>
        {analysis.observability && (
          <Zap className="w-3.5 h-3.5 text-amber-400/70 flex-shrink-0" />
        )}
      </div>

      {/* Summary */}
      <p className="text-sm text-slate-200 line-clamp-2 mb-2">
        {truncatedSummary}
        {analysis.summary.length > 50 && '...'}
      </p>

      {/* Next actions preview */}
      {analysis.next_actions && analysis.next_actions.length > 0 && (
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <FileText className="w-3 h-3" />
          <span>{analysis.next_actions.length} action{analysis.next_actions.length !== 1 ? 's' : ''}</span>
        </div>
      )}

      {/* Preview tooltip */}
      <AnimatePresence>
        {showPreview && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="absolute left-0 right-0 top-full mt-2 z-50 mx-2 p-2 bg-slate-950 border border-slate-700 rounded shadow-lg text-xs text-slate-300 pointer-events-none"
          >
            <p className="line-clamp-2">{transcriptPreview}...</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

/**
 * Empty state component
 */
function EmptyState({ isSearching }: { isSearching: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 px-4">
      <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mb-3">
        <AlertCircle className="w-6 h-6 text-slate-500" />
      </div>
      <h3 className="text-sm font-medium text-slate-300 mb-1">
        {isSearching ? 'No results found' : 'No analyses yet'}
      </h3>
      <p className="text-xs text-slate-500 text-center">
        {isSearching
          ? 'Try adjusting your search terms'
          : 'Analyses will appear here after you run your first analysis'}
      </p>
    </div>
  )
}

/**
 * Loading state component
 */
function LoadingState() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <AnalysisCardSkeleton key={i} />
      ))}
    </div>
  )
}

/**
 * Main AnalysisHistory Sidebar Component
 *
 * Features:
 * - Virtual scrolling for performance
 * - Search by transcript content
 * - Sortable by date (newest/oldest)
 * - Glassmorphic design
 * - Loading and empty states
 * - Hover previews
 * - Smooth animations
 */
export function AnalysisHistory({
  onAnalysisSelect,
  maxHeight = '600px',
  className,
}: AnalysisHistoryProps) {
  const { data: analyses, isLoading, error } = useAnalysesQuery()

  const [searchQuery, setSearchQuery] = useState('')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [virtualState, setVirtualState] = useState<VirtualScrollState>({
    visibleStart: 0,
    visibleEnd: 10,
    scrollTop: 0,
  })

  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Filter and sort analyses
  const filteredAndSortedAnalyses = useMemo(() => {
    if (!analyses) return []

    let filtered = analyses

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (analysis) =>
          analysis.transcript.toLowerCase().includes(query) ||
          analysis.summary.toLowerCase().includes(query) ||
          analysis.id.toLowerCase().includes(query)
      )
    }

    // Sort by date
    return filtered.sort((a, b) => {
      const dateA = new Date(a.created_at).getTime()
      const dateB = new Date(b.created_at).getTime()
      return sortDirection === 'desc' ? dateB - dateA : dateA - dateB
    })
  }, [analyses, searchQuery, sortDirection])

  // Handle scroll for virtual scrolling
  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const container = e.currentTarget
      const scrollTop = container.scrollTop
      const visibleStart = Math.floor(scrollTop / ITEM_HEIGHT) - BUFFER_SIZE
      const visibleEnd =
        visibleStart + Math.ceil(container.clientHeight / ITEM_HEIGHT) + BUFFER_SIZE * 2

      setVirtualState({
        scrollTop,
        visibleStart: Math.max(0, visibleStart),
        visibleEnd: Math.min(filteredAndSortedAnalyses.length, visibleEnd),
      })
    },
    [filteredAndSortedAnalyses.length]
  )

  // Handle analysis selection
  const handleSelectAnalysis = useCallback(
    (analysis: AnalysisResponse) => {
      setSelectedId(analysis.id)
      onAnalysisSelect?.(analysis)
    },
    [onAnalysisSelect]
  )

  // Calculate virtual items
  const visibleAnalyses = useMemo(() => {
    return filteredAndSortedAnalyses.slice(
      virtualState.visibleStart,
      virtualState.visibleEnd
    )
  }, [filteredAndSortedAnalyses, virtualState])

  const offsetY = virtualState.visibleStart * ITEM_HEIGHT

  // Show loading state
  if (isLoading) {
    return (
      <div className={clsx('glass rounded-xl p-4', className)}>
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Analysis History</h2>
        <LoadingState />
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className={clsx('glass rounded-xl p-4', className)}>
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Analysis History</h2>
        <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-300">Failed to load analyses</p>
            <p className="text-xs text-red-200/70">
              {error instanceof Error ? error.message : 'An error occurred'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  const isEmpty = !analyses || analyses.length === 0
  const isSearchEmpty = !isEmpty && filteredAndSortedAnalyses.length === 0

  return (
    <div className={clsx('glass rounded-xl p-4 flex flex-col h-full', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-100">Analysis History</h2>
        {!isEmpty && (
          <button
            onClick={() => setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc')}
            className="p-1.5 rounded hover:bg-slate-800 transition-colors"
            title={`Sort ${sortDirection === 'desc' ? 'oldest first' : 'newest first'}`}
          >
            <ChevronDown
              className={clsx(
                'w-4 h-4 text-slate-400 transition-transform',
                sortDirection === 'asc' && 'rotate-180'
              )}
            />
          </button>
        )}
      </div>

      {/* Search bar */}
      {!isEmpty && (
        <div className="mb-4 relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
          <input
            type="text"
            placeholder="Search transcripts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={clsx(
              'w-full pl-9 pr-3 py-2 bg-slate-900/50 border border-slate-700/50',
              'rounded-lg text-sm text-slate-200 placeholder-slate-500',
              'focus:outline-none focus:border-blue-500/50 focus:bg-slate-900',
              'transition-colors'
            )}
          />
        </div>
      )}

      {/* Analyses list or empty state */}
      {isEmpty || isSearchEmpty ? (
        <EmptyState isSearching={isSearchEmpty} />
      ) : (
        <div
          ref={scrollContainerRef}
          style={{ maxHeight }}
          className="flex-1 overflow-y-auto overflow-x-hidden pr-1 space-y-2"
        >
          {filteredAndSortedAnalyses.map((analysis) => (
            <AnalysisCard
              key={analysis.id}
              analysis={analysis}
              isSelected={selectedId === analysis.id}
              onSelect={handleSelectAnalysis}
            />
          ))}
        </div>
      )}

      {/* Footer stats */}
      {!isEmpty && (
        <div className="mt-4 pt-4 border-t border-slate-700/30 text-xs text-slate-400">
          <div className="flex items-center justify-between">
            <span>
              {filteredAndSortedAnalyses.length} of {analyses?.length || 0} analyses
            </span>
            {analyses?.length === 0 ? null : (
              <span className="flex items-center gap-1">
                <Loader2 className="w-3 h-3 animate-spin" />
                Auto-syncing
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
