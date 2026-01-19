# Component Tree & Architecture

## 📊 Component Hierarchy

```
App
├── QueryClientProvider (TanStack Query)
│   ├── ToastContainer
│   │   └── Toast[]
│   │       ├── CheckCircle2 Icon (success)
│   │       ├── XCircle Icon (error)
│   │       ├── Info Icon (info)
│   │       └── X Icon (close)
│   │
│   ├── Page Layout
│   │   ├── Header (glass-strong)
│   │   │   ├── Title (gradient-text)
│   │   │   └── Description
│   │   │
│   │   ├── Tab Navigation
│   │   │   ├── Single Analysis Tab
│   │   │   └── Batch Analysis Tab
│   │   │
│   │   ├── Content Area
│   │   │   ├── [Single Mode]
│   │   │   │   ├── TranscriptInput (glass)
│   │   │   │   │   ├── Label + CharacterCount
│   │   │   │   │   ├── Clipboard Icon Button
│   │   │   │   │   ├── Auto-expanding Textarea
│   │   │   │   │   ├── Shimmer Effect (on paste)
│   │   │   │   │   └── Error Message
│   │   │   │   │
│   │   │   │   ├── Analyze Button
│   │   │   │   │
│   │   │   │   └── AnalysisCard[] (results)
│   │   │   │       ├── Header
│   │   │   │       │   ├── Timestamp
│   │   │   │       │   ├── Analysis ID
│   │   │   │       │   └── Expand/Collapse Button
│   │   │   │       │       ├── ChevronDown Icon
│   │   │   │       │       └── ChevronUp Icon
│   │   │   │       │
│   │   │   │       ├── Summary Section
│   │   │   │       │   ├── Title
│   │   │   │       │   └── Expandable Text
│   │   │   │       │       └── (AnimatePresence)
│   │   │   │       │
│   │   │   │       ├── Next Actions Section
│   │   │   │       │   ├── Title
│   │   │   │       │   └── Action Chips[]
│   │   │   │       │       ├── Copy Icon
│   │   │   │       │       ├── Check Icon (copied)
│   │   │   │       │       └── Priority Color Border
│   │   │   │       │
│   │   │   │       ├── Observability Section (glass-strong)
│   │   │   │       │   ├── Latency Metric
│   │   │   │       │   │   ├── Clock Icon
│   │   │   │       │   │   └── Value (ms)
│   │   │   │       │   ├── Tokens Metric
│   │   │   │       │   │   ├── Zap Icon
│   │   │   │       │   │   └── Value (count)
│   │   │   │       │   ├── Cost Metric
│   │   │   │       │   │   ├── DollarSign Icon
│   │   │   │       │   │   └── Value (USD)
│   │   │   │       │   └── Model Metric
│   │   │   │       │       ├── Activity Icon
│   │   │   │       │       └── Model Name
│   │   │   │       │
│   │   │   │       └── Feedback Button
│   │   │   │
│   │   │   └── [Batch Mode]
│   │   │       └── BatchAnalyzer (glass)
│   │   │           ├── Header
│   │   │           │   ├── Title + Description
│   │   │           │   └── Valid Count
│   │   │           │
│   │   │           ├── Transcript Inputs[] (glass)
│   │   │           │   ├── Index Badge
│   │   │           │   ├── Textarea
│   │   │           │   ├── Status Icon
│   │   │           │   │   ├── Loader2 (processing)
│   │   │           │   │   ├── CheckCircle2 (success)
│   │   │           │   │   └── XCircle (error)
│   │   │           │   ├── Delete Button (Trash2 Icon)
│   │   │           │   └── Error Message (AlertCircle)
│   │   │           │
│   │   │           ├── Action Buttons
│   │   │           │   ├── Add Transcript (Plus Icon)
│   │   │           │   └── Analyze All (Play Icon / Loader2)
│   │   │           │
│   │   │           └── Results Summary (glass-strong)
│   │   │               ├── Total Count
│   │   │               ├── Successful Count
│   │   │               ├── Failed Count
│   │   │               └── Error List[] (AlertCircle)
│   │   │
│   │   └── FeedbackModal (portal)
│   │       ├── Backdrop (blur)
│   │       └── Modal Container (glass-strong)
│   │           ├── Header
│   │           │   ├── Title + Description
│   │           │   └── Close Button (X Icon)
│   │           │
│   │           ├── Form
│   │           │   ├── Star Rating
│   │           │   │   ├── Star Icons[5]
│   │           │   │   └── Rating Label
│   │           │   │
│   │           │   ├── Hallucination Toggle (glass)
│   │           │   │   ├── Checkbox
│   │           │   │   ├── AlertTriangle Icon
│   │           │   │   └── Description
│   │           │   │
│   │           │   ├── Comment Textarea
│   │           │   │   ├── Label
│   │           │   │   ├── Textarea (glass)
│   │           │   │   └── Character Count
│   │           │   │
│   │           │   ├── Error Message (AlertTriangle)
│   │           │   │
│   │           │   └── Action Buttons
│   │           │       ├── Cancel Button
│   │           │       └── Submit Button
│   │           │           ├── Send Icon
│   │           │           └── Loader2 (submitting)
│   │           │
│   │           └── (AnimatePresence for animations)
│   │
│   └── Custom Hooks
│       ├── useToast()
│       ├── useDebounce()
│       ├── useLoading()
│       ├── useKeyboardShortcut()
│       ├── useClickOutside()
│       ├── useLocalStorage()
│       ├── useMediaQuery()
│       └── useScrollLock()
```

---

## 🎨 Component Styling Architecture

```
Global Styles (globals.css)
├── Base Layer
│   ├── CSS Variables
│   │   ├── --font-inter
│   │   ├── --font-playfair
│   │   ├── --background
│   │   └── --foreground
│   │
│   └── Base Element Styles
│       ├── * (border color)
│       └── body (font family)
│
└── Utilities Layer
    ├── Glassmorphism
    │   ├── .glass (light blur)
    │   └── .glass-strong (heavy blur)
    │
    ├── Animations
    │   └── .shimmer (2s infinite)
    │
    └── Effects
        └── .gradient-text (blue→purple→pink)
```

---

## 🔄 Data Flow Architecture

```
User Interaction
    ↓
Component Event Handler
    ↓
Custom Hook (useLoading, useToast, etc.)
    ↓
API Client (lib/api-client.ts)
    ↓
Backend API
    ↓
Response Processing
    ↓
State Update (React useState)
    ↓
Component Re-render
    ↓
UI Update (with Framer Motion animations)
    ↓
Toast Notification (success/error)
```

---

## 📦 Import/Export Structure

```
@/components/index.ts (Barrel Export)
├── export { default as AnalysisCard } from './AnalysisCard'
├── export { default as TranscriptInput } from './TranscriptInput'
├── export { default as BatchAnalyzer } from './BatchAnalyzer'
├── export { default as FeedbackModal } from './FeedbackModal'
└── export * from './hooks'
    ├── useToast
    ├── useDebounce
    ├── useLoading
    ├── useKeyboardShortcut
    ├── useClickOutside
    ├── useLocalStorage
    ├── useMediaQuery
    └── useScrollLock
```

---

## 🎯 State Management Strategy

### Local State (useState)
```
Component Internal State
├── AnalysisCard
│   ├── isExpanded: boolean
│   └── copiedIndex: number | null
│
├── TranscriptInput
│   ├── isPasteShimmering: boolean
│   └── height: number
│
├── BatchAnalyzer
│   ├── transcripts: TranscriptItem[]
│   ├── isProcessing: boolean
│   └── results: BatchAnalysisResponse | null
│
└── FeedbackModal
    ├── rating: number
    ├── hoveredRating: number
    ├── isHallucination: boolean
    ├── comment: string
    ├── isSubmitting: boolean
    └── error: string | null
```

### Global State (Custom Hooks)
```
useToast()
├── toasts: Toast[]
└── addToast: (message, type) => void

useLoading()
├── isLoading: boolean
├── error: Error | null
└── wrap: <T>(fn: () => Promise<T>) => Promise<T | null>
```

### Server State (TanStack Query)
```
QueryClient
├── Cache
│   ├── analyses
│   ├── metrics
│   └── health
│
├── Mutations
│   ├── analyzeTranscript
│   ├── batchAnalyze
│   └── submitFeedback
│
└── Query Keys
    ├── ['analyses']
    ├── ['analyses', id]
    └── ['metrics']
```

---

## 🎭 Animation Patterns

### Entry Animations
```
Component Mount
    ↓
initial={{ opacity: 0, y: 20 }}
    ↓
animate={{ opacity: 1, y: 0 }}
    ↓
transition={{ duration: 0.4, ease: 'easeOut' }}
    ↓
Visible Component
```

### Modal Animations
```
Modal Open
    ↓
Backdrop: opacity 0 → 1
    ↓
Modal: scale 0.95 → 1, y 20 → 0
    ↓
AnimatePresence manages exit
    ↓
Modal Close (reverse animation)
```

### List Animations
```
Item Added
    ↓
initial={{ opacity: 0, y: -10 }}
    ↓
animate={{ opacity: 1, y: 0 }}
    ↓
Stagger delay: index * 0.1
    ↓
exit={{ opacity: 0, x: -100 }}
```

---

## ♿ Accessibility Tree

```
Application
├── [role="banner"] Header
│   ├── [role="heading" level="1"] Title
│   └── [role="text"] Description
│
├── [role="navigation"] Tab Navigation
│   ├── [role="tab" aria-selected="true"] Active Tab
│   └── [role="tab" aria-selected="false"] Inactive Tab
│
├── [role="main"] Content Area
│   ├── [role="form"] Input Form
│   │   ├── [role="textbox" aria-label="..."] Textarea
│   │   ├── [aria-live="polite"] Character Count
│   │   └── [role="button"] Submit Button
│   │
│   ├── [role="region"] Results Section
│   │   └── [role="article" aria-label="..."] AnalysisCard[]
│   │       ├── [role="complementary"] Observability
│   │       └── [role="button"] Feedback Button
│   │
│   └── [role="dialog" aria-modal="true"] FeedbackModal
│       ├── [role="radiogroup"] Star Rating
│       ├── [role="checkbox"] Hallucination Toggle
│       └── [role="button"] Submit/Cancel
│
└── [aria-live="polite" aria-atomic="true"] Toast Container
    └── [role="alert"] Toast[]
```

---

## 🔌 Integration Points

### Backend API Integration
```
Component
    ↓
lib/api-client.ts
    ↓
fetch(NEXT_PUBLIC_API_URL/endpoint)
    ↓
Response → types/api.ts
    ↓
Component State Update
```

### Type Safety Flow
```
Backend (Pydantic Models)
    ↓
types/api.ts (TypeScript Interfaces)
    ↓
Components (Typed Props)
    ↓
API Client (Type-safe Methods)
    ↓
Runtime Validation
```

---

## 📱 Responsive Behavior

### Breakpoints
```
Mobile (< 640px)
├── Single column layout
├── Full-width components
├── Stacked action buttons
└── Compact metrics grid

Tablet (640px - 1024px)
├── Flexible layouts
├── Side-by-side elements
├── 2-column grids
└── Responsive typography

Desktop (> 1024px)
├── Multi-column layouts
├── Maximum widths enforced
├── 4-column metric grids
└── Expanded information density
```

---

## 🎯 Component Communication

### Parent → Child (Props)
```
Page Component
    ↓ props
Child Components
    ↓ render
UI Elements
```

### Child → Parent (Callbacks)
```
User Action
    ↓ event
Component Handler
    ↓ callback prop
Parent State Update
    ↓ re-render
UI Sync
```

### Sibling Communication (Lifted State)
```
Component A
    ↑ callback    ↓ props
    Parent State
    ↓ props       ↑ callback
Component B
```

---

## 🔄 Lifecycle Patterns

### Component Lifecycle
```
1. Mount
   ├── Initialize state
   ├── Set up refs
   ├── Attach event listeners (useEffect)
   └── Trigger entrance animations

2. Update
   ├── Props change
   ├── State change
   ├── Auto-resize (textarea)
   └── Animate transitions

3. Unmount
   ├── Exit animations (AnimatePresence)
   ├── Cleanup event listeners
   ├── Clear timers
   └── Release resources
```

---

This component tree provides a complete architectural overview of the glassmorphic UI system, showing all relationships, data flows, and integration points.
