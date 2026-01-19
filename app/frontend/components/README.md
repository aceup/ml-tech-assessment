# Premium Glassmorphic UI Components

A collection of premium, accessible React components with glassmorphic design for the ML Tech Assessment project.

## Components

### 1. AnalysisCard

A sophisticated card component for displaying analysis results with expandable content and observability metrics.

**Features:**
- ✨ Glassmorphic design with blur effects
- 📊 Expandable summary with Framer Motion animations
- 🎯 Interactive action chips with priority colors (high/medium/low)
- 📋 Copy-to-clipboard functionality with visual feedback
- 📈 Observability metadata display (tokens, latency, cost, model)
- ♿ Fully accessible with ARIA labels
- 🎨 Responsive grid layout for metrics

**Props:**
```typescript
interface AnalysisCardProps {
  analysis: AnalysisResponse
  onFeedback?: (analysisId: string) => void
}
```

**Usage:**
```tsx
import { AnalysisCard } from '@/components'

<AnalysisCard
  analysis={analysisData}
  onFeedback={(id) => console.log('Feedback for:', id)}
/>
```

---

### 2. TranscriptInput

A smart, auto-expanding textarea with character counting and paste functionality.

**Features:**
- 📝 Auto-expanding textarea (min/max height)
- 🔢 Real-time character count with color-coded limits
- 📋 Paste-from-clipboard button
- ✨ Shimmer effect on paste action
- 💀 Loading skeleton states
- ⚠️ Error state handling
- ♿ Accessible with proper ARIA attributes

**Props:**
```typescript
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
```

**Usage:**
```tsx
import { TranscriptInput } from '@/components'

<TranscriptInput
  value={transcript}
  onChange={setTranscript}
  maxLength={5000}
  placeholder="Enter transcript..."
  label="Medical Transcript"
/>
```

---

### 3. BatchAnalyzer

A powerful batch processing interface for analyzing multiple transcripts simultaneously.

**Features:**
- 📚 Multi-transcript input management
- ➕ Add/remove transcript inputs dynamically
- ▶️ Batch analysis execution
- 📊 Real-time progress indicators
- ✅ Success/failure status icons
- 📈 Results summary (total/successful/failed)
- ⚠️ Error reporting per transcript
- 🎨 Animated list with Framer Motion

**Props:**
```typescript
interface BatchAnalyzerProps {
  onAnalyze: (transcripts: string[]) => Promise<BatchAnalysisResponse>
  maxTranscripts?: number
  minTranscriptLength?: number
}
```

**Usage:**
```tsx
import { BatchAnalyzer } from '@/components'

<BatchAnalyzer
  onAnalyze={handleBatchAnalyze}
  maxTranscripts={10}
  minTranscriptLength={10}
/>
```

---

### 4. FeedbackModal

A comprehensive feedback modal with star ratings and hallucination reporting.

**Features:**
- ⭐ 5-star rating system with hover effects
- ⚠️ Hallucination checkbox with description
- 💬 Optional comment textarea (500 chars)
- 🎭 Backdrop blur with click-outside to close
- ⚡ Form validation
- 🔄 Loading states during submission
- ♿ Fully accessible modal with proper ARIA roles
- 🎨 Scale animations with Framer Motion

**Props:**
```typescript
interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (feedback: EvaluationRequest) => Promise<void>
  analysisId: string
}
```

**Usage:**
```tsx
import { FeedbackModal } from '@/components'

<FeedbackModal
  isOpen={showModal}
  onClose={() => setShowModal(false)}
  onSubmit={handleFeedbackSubmit}
  analysisId="analysis-123"
/>
```

---

### 5. Toast / ToastContainer

Notification components for user feedback.

**Features:**
- 🎯 Three types: success, error, info
- 🎨 Color-coded with appropriate icons
- ⏱️ Auto-dismiss after 3 seconds
- 🎭 Smooth animations with Framer Motion
- ♿ Accessible with aria-live regions

**Usage:**
```tsx
import { useToast } from '@/components/hooks'
import { ToastContainer } from '@/components/Toast'

function MyComponent() {
  const { toasts, addToast } = useToast()

  return (
    <>
      <button onClick={() => addToast('Success!', 'success')}>
        Show Toast
      </button>
      <ToastContainer toasts={toasts} onClose={(id) => {}} />
    </>
  )
}
```

---

## Custom Hooks

### useToast()
Manages toast notifications with auto-dismiss.

### useDebounce(value, delay)
Debounces value changes for performance optimization.

### useLoading()
Manages loading states with error handling.

### useKeyboardShortcut(key, callback, modifiers)
Registers keyboard shortcuts with modifier support.

### useClickOutside(ref, callback)
Detects clicks outside a referenced element.

### useLocalStorage(key, initialValue)
Syncs state with localStorage.

### useMediaQuery(query)
Detects media query matches for responsive design.

### useScrollLock(isLocked)
Locks body scroll (useful for modals).

---

## Design System

### Glassmorphism Classes

The components use custom Tailwind utility classes defined in `app/globals.css`:

**`.glass`** - Standard glassmorphic effect
- Background: `rgba(15, 23, 42, 0.5)`
- Backdrop blur: `12px`
- Border: `1px solid rgba(148, 163, 184, 0.1)`

**`.glass-strong`** - Stronger glassmorphic effect
- Background: `rgba(15, 23, 42, 0.8)`
- Backdrop blur: `16px`
- Border: `1px solid rgba(148, 163, 184, 0.15)`

**`.shimmer`** - Shimmer animation
- 2-second infinite animation
- Gradient effect from left to right

**`.gradient-text`** - Gradient text effect
- Blue → Purple → Pink gradient
- Background-clip for text effect

### Priority Colors

Used in action chips and status indicators:

- **High priority**: Red (`bg-red-500/20`, `text-red-300`, `border-red-500/30`)
- **Medium priority**: Yellow (`bg-yellow-500/20`, `text-yellow-300`, `border-yellow-500/30`)
- **Low priority**: Green (`bg-green-500/20`, `text-green-300`, `border-green-500/30`)

---

## Accessibility Features

All components follow WCAG 2.1 Level AA guidelines:

- ✅ Semantic HTML elements
- ✅ ARIA labels and descriptions
- ✅ Keyboard navigation support
- ✅ Focus management
- ✅ Screen reader announcements (aria-live)
- ✅ Color contrast ratios
- ✅ Focus visible indicators

---

## Animation Details

### Framer Motion Patterns

**Card entrance:**
```tsx
initial={{ opacity: 0, y: 20 }}
animate={{ opacity: 1, y: 0 }}
transition={{ duration: 0.4, ease: 'easeOut' }}
```

**Expand/collapse:**
```tsx
initial={{ opacity: 0, height: 0 }}
animate={{ opacity: 1, height: 'auto' }}
exit={{ opacity: 0, height: 0 }}
transition={{ duration: 0.3 }}
```

**Modal:**
```tsx
initial={{ opacity: 0, scale: 0.95, y: 20 }}
animate={{ opacity: 1, scale: 1, y: 0 }}
exit={{ opacity: 0, scale: 0.95, y: 20 }}
transition={{ duration: 0.2 }}
```

**Hover effects:**
```tsx
whileHover={{ scale: 1.1 }}
whileTap={{ scale: 0.95 }}
```

---

## Dependencies

- **React 19** - Latest React with concurrent features
- **Next.js 16** - Server/client components
- **Framer Motion 11** - Animation library
- **Lucide React** - Icon library
- **Tailwind CSS 4** - Utility-first CSS
- **TypeScript 5** - Type safety

---

## File Structure

```
frontend/components/
├── AnalysisCard.tsx      # Analysis result display
├── TranscriptInput.tsx   # Smart textarea input
├── BatchAnalyzer.tsx     # Batch processing UI
├── FeedbackModal.tsx     # Feedback submission modal
├── Toast.tsx             # Toast notification
├── hooks.ts              # Custom React hooks
├── index.ts              # Export barrel
└── README.md             # This file
```

---

## Demo Page

Visit `/demo` to see all components in action with live API integration.

**Features:**
- Single analysis mode
- Batch analysis mode
- Tab navigation
- Live toast notifications
- Full integration with backend API

---

## Best Practices

### Performance
- Use `React.memo()` for expensive components
- Debounce input changes
- Lazy load modal content
- Optimize animations with `will-change`

### Accessibility
- Always provide `aria-label` for icon buttons
- Use semantic HTML (`<article>`, `<section>`, `<header>`)
- Manage focus for modals and dropdowns
- Test with screen readers

### Styling
- Use glassmorphic effects sparingly
- Maintain consistent spacing (Tailwind scale)
- Test dark mode compatibility
- Ensure 4.5:1 color contrast minimum

---

## Future Enhancements

- [ ] Dark/light mode toggle
- [ ] Component theming system
- [ ] Animation customization props
- [ ] Export to Storybook
- [ ] Unit tests with Jest + RTL
- [ ] E2E tests with Playwright
- [ ] Internationalization (i18n)
- [ ] Mobile gesture support

---

## License

MIT License - Part of ML Tech Assessment Project

---

## Support

For issues or questions about these components, please refer to the main project documentation or create an issue in the repository.
