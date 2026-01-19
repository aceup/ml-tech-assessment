'use client'

/**
 * Analytics Dashboard Component
 *
 * Displays comprehensive analytics including cost metrics, token usage,
 * latency charts, quality scores, and provider breakdown.
 *
 * Features:
 * - Glassmorphic card design
 * - Animated number count-ups
 * - Color-coded metrics (green/amber/red)
 * - Responsive grid layout
 * - Loading skeleton states
 * - Error boundaries with Recharts visualizations
 */

import { useAnalyticsQuery } from '@/lib/queries'
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { useEffect, useState } from 'react'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Zap,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Activity,
  Database,
  List,
} from 'lucide-react'
import DetailedAnalyticsModal from './DetailedAnalyticsModal'

// Color palette for dark theme
const COLORS = {
  primary: '#3b82f6', // blue-500
  success: '#10b981', // green-500
  warning: '#f59e0b', // amber-500
  danger: '#ef4444', // red-500
  purple: '#8b5cf6', // purple-500
  cyan: '#06b6d4', // cyan-500
  pink: '#ec4899', // pink-500
  indigo: '#6366f1', // indigo-500
}

const PROVIDER_COLORS = [
  COLORS.primary,
  COLORS.purple,
  COLORS.cyan,
  COLORS.pink,
  COLORS.indigo,
]

interface AnimatedNumberProps {
  value: number
  duration?: number
  decimals?: number
  prefix?: string
  suffix?: string
}

function AnimatedNumber({
  value,
  duration = 1000,
  decimals = 0,
  prefix = '',
  suffix = '',
}: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    const startTime = Date.now()
    const startValue = 0

    const animate = () => {
      const currentTime = Date.now()
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)

      // Easing function (ease-out cubic)
      const easeOut = 1 - Math.pow(1 - progress, 3)
      const currentValue = startValue + (value - startValue) * easeOut

      setDisplayValue(currentValue)

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    animate()
  }, [value, duration])

  return (
    <span>
      {prefix}
      {displayValue.toFixed(decimals)}
      {suffix}
    </span>
  )
}

interface MetricCardProps {
  title: string
  value: number | string
  icon: React.ReactNode
  change?: number
  trend?: 'up' | 'down'
  color?: 'success' | 'warning' | 'danger' | 'primary'
  subtitle?: string
  animated?: boolean
  decimals?: number
  prefix?: string
  suffix?: string
}

function MetricCard({
  title,
  value,
  icon,
  change,
  trend,
  color = 'primary',
  subtitle,
  animated = true,
  decimals = 0,
  prefix = '',
  suffix = '',
}: MetricCardProps) {
  const colorClasses = {
    success: 'text-green-500 bg-green-500/10 border-green-500/20',
    warning: 'text-amber-500 bg-amber-500/10 border-amber-500/20',
    danger: 'text-red-500 bg-red-500/10 border-red-500/20',
    primary: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
  }

  return (
    <div className="relative overflow-hidden rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl transition-all hover:border-white/20 hover:bg-white/10">
      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent" />

      <div className="relative">
        <div className="flex items-center justify-between">
          <div
            className={`rounded-lg p-3 ${colorClasses[color].split(' ').slice(1).join(' ')}`}
          >
            {icon}
          </div>
          {change !== undefined && trend && (
            <div
              className={`flex items-center gap-1 text-sm ${
                trend === 'up' ? 'text-green-500' : 'text-red-500'
              }`}
            >
              {trend === 'up' ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span>{Math.abs(change).toFixed(1)}%</span>
            </div>
          )}
        </div>

        <div className="mt-4">
          <p className="text-sm text-zinc-400">{title}</p>
          <p className={`mt-2 text-3xl font-bold ${colorClasses[color].split(' ')[0]}`}>
            {animated && typeof value === 'number' ? (
              <AnimatedNumber
                value={value}
                decimals={decimals}
                prefix={prefix}
                suffix={suffix}
              />
            ) : (
              `${prefix}${value}${suffix}`
            )}
          </p>
          {subtitle && <p className="mt-1 text-xs text-zinc-500">{subtitle}</p>}
        </div>
      </div>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <div className="h-12 w-12 rounded-lg bg-white/10" />
        <div className="h-6 w-16 rounded bg-white/10" />
      </div>
      <div className="mt-4 space-y-2">
        <div className="h-4 w-24 rounded bg-white/10" />
        <div className="h-8 w-32 rounded bg-white/10" />
        <div className="h-3 w-20 rounded bg-white/10" />
      </div>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-6 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <AlertTriangle className="h-6 w-6 text-red-500" />
        <div>
          <h3 className="font-semibold text-red-500">Error Loading Analytics</h3>
          <p className="mt-1 text-sm text-red-400">{message}</p>
        </div>
      </div>
    </div>
  )
}

export default function AnalyticsDashboard() {
  const { data: analytics, isLoading, error } = useAnalyticsQuery()
  const [showDetailedModal, setShowDetailedModal] = useState(false)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <div
              key={i}
              className="h-80 animate-pulse rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl"
            />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return <ErrorState message={error.message || 'Failed to load analytics data'} />
  }

  if (!analytics) {
    return <ErrorState message="No analytics data available" />
  }

  // Prepare latency data for chart
  const latencyData = [
    { name: 'Average', value: analytics.avg_latency_ms, color: COLORS.primary },
    { name: 'P50 (Median)', value: analytics.p50_latency_ms, color: COLORS.success },
    { name: 'P95', value: analytics.p95_latency_ms, color: COLORS.warning },
    { name: 'P99', value: analytics.p99_latency_ms, color: COLORS.danger },
  ]

  // Prepare provider breakdown for pie chart
  const providerData = Object.entries(analytics.provider_breakdown || {}).map(
    ([name, value]) => ({
      name,
      value,
    })
  )

  // Token usage data for bar chart
  const tokenData = [
    {
      name: 'Input',
      total: analytics.total_input_tokens,
      average: analytics.avg_input_tokens,
    },
    {
      name: 'Output',
      total: analytics.total_output_tokens,
      average: analytics.avg_output_tokens,
    },
  ]

  // Calculate quality color
  const getQualityColor = (score?: number): 'success' | 'warning' | 'danger' => {
    if (!score) return 'warning'
    if (score >= 0.8) return 'success'
    if (score >= 0.6) return 'warning'
    return 'danger'
  }

  // Calculate hallucination color
  const getHallucinationColor = (
    rate?: number
  ): 'success' | 'warning' | 'danger' => {
    if (!rate) return 'success'
    if (rate <= 0.05) return 'success'
    if (rate <= 0.15) return 'warning'
    return 'danger'
  }

  return (
    <div className="space-y-4">
      {/* Key Metrics - Compact 2-column Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="glass-strong rounded-lg p-3 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <div className="rounded bg-blue-500/10 p-1.5">
              <Database className="h-4 w-4 text-blue-500" />
            </div>
            <span className="text-xs text-slate-400 font-medium">Analyses</span>
          </div>
          <p className="text-2xl font-bold text-blue-400">
            <AnimatedNumber value={analytics.total_analyses} decimals={0} />
          </p>
        </div>

        <div className="glass-strong rounded-lg p-3 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <div className="rounded bg-green-500/10 p-1.5">
              <DollarSign className="h-4 w-4 text-green-500" />
            </div>
            <span className="text-xs text-slate-400 font-medium">Cost</span>
          </div>
          <p className="text-2xl font-bold text-green-400">
            <AnimatedNumber
              value={analytics.total_cost_usd}
              decimals={4}
              prefix="$"
            />
          </p>
          <p className="text-xs text-slate-500 mt-1">
            ${analytics.cost_per_1000_requests.toFixed(4)}/1K
          </p>
        </div>

        <div className="glass-strong rounded-lg p-3 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <div className="rounded bg-amber-500/10 p-1.5">
              <Clock className="h-4 w-4 text-amber-500" />
            </div>
            <span className="text-xs text-slate-400 font-medium">Avg Latency</span>
          </div>
          <p className={`text-2xl font-bold ${
            analytics.avg_latency_ms < 1000 ? 'text-green-400' : 'text-amber-400'
          }`}>
            <AnimatedNumber
              value={analytics.avg_latency_ms}
              decimals={0}
              suffix=" ms"
            />
          </p>
          <p className="text-xs text-slate-500 mt-1">Response time</p>
        </div>

        <div className="glass-strong rounded-lg p-3 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <div className="rounded bg-purple-500/10 p-1.5">
              <CheckCircle2 className="h-4 w-4 text-purple-500" />
            </div>
            <span className="text-xs text-slate-400 font-medium">Evals</span>
          </div>
          <p className="text-2xl font-bold text-purple-400">
            <AnimatedNumber value={analytics.total_evaluations} decimals={0} />
          </p>
        </div>
      </div>

      {/* Quality Metrics */}
      {analytics.avg_score !== null && analytics.avg_score !== undefined && (
        <div className="grid grid-cols-2 gap-3">
          <div className="glass-strong rounded-lg p-3 border border-white/10">
            <div className="flex items-center gap-2 mb-2">
              <div className={`rounded p-1.5 ${
                getQualityColor(analytics.avg_score) === 'success' ? 'bg-green-500/10' :
                getQualityColor(analytics.avg_score) === 'warning' ? 'bg-amber-500/10' :
                'bg-red-500/10'
              }`}>
                <Activity className={`h-4 w-4 ${
                  getQualityColor(analytics.avg_score) === 'success' ? 'text-green-500' :
                  getQualityColor(analytics.avg_score) === 'warning' ? 'text-amber-500' :
                  'text-red-500'
                }`} />
              </div>
              <span className="text-xs text-slate-400 font-medium">Quality</span>
            </div>
            <p className={`text-2xl font-bold ${
              getQualityColor(analytics.avg_score) === 'success' ? 'text-green-400' :
              getQualityColor(analytics.avg_score) === 'warning' ? 'text-amber-400' :
              'text-red-400'
            }`}>
              <AnimatedNumber value={analytics.avg_score} decimals={2} />
            </p>
            <p className="text-xs text-slate-500 mt-1">Avg score</p>
          </div>

          <div className="glass-strong rounded-lg p-3 border border-white/10">
            <div className="flex items-center gap-2 mb-2">
              <div className={`rounded p-1.5 ${
                getHallucinationColor(analytics.hallucination_rate) === 'success' ? 'bg-green-500/10' :
                getHallucinationColor(analytics.hallucination_rate) === 'warning' ? 'bg-amber-500/10' :
                'bg-red-500/10'
              }`}>
                <AlertTriangle className={`h-4 w-4 ${
                  getHallucinationColor(analytics.hallucination_rate) === 'success' ? 'text-green-500' :
                  getHallucinationColor(analytics.hallucination_rate) === 'warning' ? 'text-amber-500' :
                  'text-red-500'
                }`} />
              </div>
              <span className="text-xs text-slate-400 font-medium">False Info</span>
            </div>
            <p className={`text-2xl font-bold ${
              getHallucinationColor(analytics.hallucination_rate) === 'success' ? 'text-green-400' :
              getHallucinationColor(analytics.hallucination_rate) === 'warning' ? 'text-amber-400' :
              'text-red-400'
            }`}>
              <AnimatedNumber
                value={(analytics.hallucination_rate || 0) * 100}
                decimals={2}
                suffix="%"
              />
            </p>
            <p className="text-xs text-slate-500 mt-1">Incorrect data</p>
          </div>
        </div>
      )}

      {/* Compact Charts */}
      <div className="space-y-3">
        {/* Latency Chart - Compact */}
        <div className="glass-strong rounded-lg p-3 border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <div className="rounded bg-blue-500/10 p-1">
              <Clock className="h-3.5 w-3.5 text-blue-500" />
            </div>
            <span className="text-xs text-slate-400 font-medium">Latency</span>
          </div>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
              <XAxis dataKey="name" stroke="#9ca3af" fontSize={10} />
              <YAxis stroke="#9ca3af" fontSize={10} width={30} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(0, 0, 0, 0.9)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  fontSize: '11px',
                }}
                labelStyle={{ color: '#fff' }}
                itemStyle={{ color: '#e5e7eb' }}
                formatter={(value: number) => [`${value.toFixed(0)}ms`, '']}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {latencyData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Token Usage - Compact */}
        <div className="glass-strong rounded-lg p-3 border border-white/10">
          <div className="flex items-center gap-2 mb-3">
            <div className="rounded bg-cyan-500/10 p-1">
              <Activity className="h-3.5 w-3.5 text-cyan-500" />
            </div>
            <span className="text-xs text-slate-400 font-medium">Token Usage</span>
          </div>
          <div className="space-y-3">
            {/* Input Tokens */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-400">Input</span>
                <span className="text-xs font-semibold text-blue-400">
                  {analytics.total_input_tokens.toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-slate-800/50 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full transition-all duration-500"
                  style={{
                    width: `${
                      (analytics.total_input_tokens /
                        (analytics.total_input_tokens + analytics.total_output_tokens)) *
                      100
                    }%`,
                  }}
                />
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                Avg: {analytics.avg_input_tokens.toLocaleString()}
              </div>
            </div>

            {/* Output Tokens */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-400">Output</span>
                <span className="text-xs font-semibold text-purple-400">
                  {analytics.total_output_tokens.toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-slate-800/50 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500"
                  style={{
                    width: `${
                      (analytics.total_output_tokens /
                        (analytics.total_input_tokens + analytics.total_output_tokens)) *
                      100
                    }%`,
                  }}
                />
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                Avg: {analytics.avg_output_tokens.toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        {/* Provider Distribution - Compact */}
        {providerData.length > 0 && (
          <div className="glass-strong rounded-lg p-3 border border-white/10">
            <div className="flex items-center gap-2 mb-2">
              <div className="rounded bg-purple-500/10 p-1">
                <Zap className="h-3.5 w-3.5 text-purple-500" />
              </div>
              <span className="text-xs text-slate-400 font-medium">Providers</span>
            </div>
            <div className="flex items-center gap-3">
              <ResponsiveContainer width="40%" height={80}>
                <PieChart>
                  <Pie
                    data={providerData}
                    cx="50%"
                    cy="50%"
                    innerRadius={20}
                    outerRadius={35}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {providerData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={PROVIDER_COLORS[index % PROVIDER_COLORS.length]}
                      />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-1">
                {providerData.map((provider, index) => (
                  <div key={provider.name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{
                          backgroundColor: PROVIDER_COLORS[index % PROVIDER_COLORS.length],
                        }}
                      />
                      <span className="text-slate-300">{provider.name}</span>
                    </div>
                    <span className="text-slate-400">{provider.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Detailed Analytics Button */}
      <button
        onClick={() => setShowDetailedModal(true)}
        className="w-full glass-strong rounded-lg border border-white/10 p-3 hover:bg-white/5 transition-colors flex items-center justify-center gap-2"
      >
        <List className="h-4 w-4 text-blue-400" />
        <span className="text-sm font-medium text-slate-300">
          View Detailed Analytics
        </span>
      </button>

      {/* Detailed Analytics Modal */}
      <DetailedAnalyticsModal
        isOpen={showDetailedModal}
        onClose={() => setShowDetailedModal(false)}
      />
    </div>
  )
}
