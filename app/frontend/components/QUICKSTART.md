# Component Quick Start Guide

## Installation

All components are ready to use. Import from `/components`:

```tsx
import {
  AnalysisCard,
  TranscriptInput,
  BatchAnalyzer,
  FeedbackModal,
  useToast,
  useDebounce,
  useLoading,
} from '@/components'
```

---

## 1-Minute Examples

### Display an Analysis Result

```tsx
'use client'

import { AnalysisCard } from '@/components'

export default function MyPage() {
  const analysis = {
    id: '123',
    summary: 'Patient presents with acute symptoms...',
    next_actions: ['Order blood tests', 'Schedule follow-up', 'Prescribe medication'],
    created_at: new Date().toISOString(),
    transcript: 'Original transcript...',
    observability: {
      llm_provider: 'anthropic',
      llm_model: 'claude-3.5-sonnet',
      input_tokens: 1500,
      output_tokens: 300,
      latency_ms: 1200,
    },
  }

  return <AnalysisCard analysis={analysis} onFeedback={(id) => alert(id)} />
}
```

---

### Smart Transcript Input

```tsx
'use client'

import { useState } from 'react'
import { TranscriptInput } from '@/components'

export default function InputPage() {
  const [text, setText] = useState('')

  return (
    <TranscriptInput
      value={text}
      onChange={setText}
      placeholder="Paste or type transcript..."
      maxLength={5000}
    />
  )
}
```

---

### Batch Analyzer

```tsx
'use client'

import { BatchAnalyzer } from '@/components'
import { apiClient } from '@/lib/api-client'

export default function BatchPage() {
  return (
    <BatchAnalyzer
      onAnalyze={async (transcripts) => {
        return await apiClient.batchAnalyze(transcripts)
      }}
      maxTranscripts={10}
    />
  )
}
```

---

### Feedback Modal

```tsx
'use client'

import { useState } from 'react'
import { FeedbackModal } from '@/components'
import { apiClient } from '@/lib/api-client'

export default function FeedbackPage() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button onClick={() => setIsOpen(true)}>Give Feedback</button>

      <FeedbackModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        analysisId="analysis-123"
        onSubmit={async (feedback) => {
          await apiClient.submitFeedback('analysis-123', feedback)
        }}
      />
    </>
  )
}
```

---

### Toast Notifications

```tsx
'use client'

import { useToast } from '@/components'
import { ToastContainer } from '@/components/Toast'

export default function ToastPage() {
  const { toasts, addToast } = useToast()

  return (
    <>
      <button onClick={() => addToast('Success!', 'success')}>
        Show Success
      </button>
      <button onClick={() => addToast('Error!', 'error')}>
        Show Error
      </button>

      <ToastContainer
        toasts={toasts}
        onClose={(id) => {
          // Optional: handle toast close
        }}
      />
    </>
  )
}
```

---

## Complete Integration Example

```tsx
'use client'

import { useState } from 'react'
import {
  AnalysisCard,
  TranscriptInput,
  FeedbackModal,
  useToast,
  useLoading,
} from '@/components'
import { ToastContainer } from '@/components/Toast'
import { apiClient } from '@/lib/api-client'
import type { AnalysisResponse } from '@/types/api'

export default function AnalysisPage() {
  const [transcript, setTranscript] = useState('')
  const [analyses, setAnalyses] = useState<AnalysisResponse[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { toasts, addToast } = useToast()
  const { isLoading, wrap } = useLoading()

  const handleAnalyze = async () => {
    const result = await wrap(async () => {
      return await apiClient.analyzeTranscript(transcript)
    })

    if (result) {
      setAnalyses([result, ...analyses])
      setTranscript('')
      addToast('Analysis complete!', 'success')
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8">
      {/* Input */}
      <section className="glass rounded-2xl p-6">
        <TranscriptInput
          value={transcript}
          onChange={setTranscript}
          isLoading={isLoading}
        />
        <button
          onClick={handleAnalyze}
          disabled={isLoading}
          className="mt-4 w-full glass-strong rounded-lg py-3 bg-blue-500/20 text-blue-300"
        >
          {isLoading ? 'Analyzing...' : 'Analyze'}
        </button>
      </section>

      {/* Results */}
      <section className="space-y-4">
        {analyses.map((analysis) => (
          <AnalysisCard
            key={analysis.id}
            analysis={analysis}
            onFeedback={setSelectedId}
          />
        ))}
      </section>

      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={selectedId !== null}
        onClose={() => setSelectedId(null)}
        analysisId={selectedId || ''}
        onSubmit={async (feedback) => {
          await apiClient.submitFeedback(selectedId!, feedback)
          addToast('Feedback submitted!', 'success')
        }}
      />

      {/* Toasts */}
      <ToastContainer toasts={toasts} onClose={() => {}} />
    </div>
  )
}
```

---

## Styling Tips

### Custom Glassmorphic Effects

```css
/* Lighter glass */
.glass-light {
  background: rgba(15, 23, 42, 0.3);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(148, 163, 184, 0.05);
}

/* Extra strong glass */
.glass-extra {
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(148, 163, 184, 0.2);
}
```

### Custom Priority Colors

```tsx
const customColors = {
  critical: 'bg-red-600/30 text-red-200 border-red-600/40',
  warning: 'bg-amber-500/30 text-amber-200 border-amber-500/40',
  normal: 'bg-blue-500/30 text-blue-200 border-blue-500/40',
}
```

---

## Common Patterns

### Debounced Search

```tsx
import { useState } from 'react'
import { TranscriptInput, useDebounce } from '@/components'

function SearchInput() {
  const [value, setValue] = useState('')
  const debouncedValue = useDebounce(value, 500)

  // Use debouncedValue for API calls
  useEffect(() => {
    if (debouncedValue) {
      // Perform search
    }
  }, [debouncedValue])

  return <TranscriptInput value={value} onChange={setValue} />
}
```

### Loading States

```tsx
import { useLoading } from '@/components'

function MyComponent() {
  const { isLoading, error, wrap } = useLoading()

  const handleAction = async () => {
    const result = await wrap(async () => {
      return await apiClient.analyzeTranscript('...')
    })

    if (result) {
      // Handle success
    }
    // Error is automatically stored in `error` state
  }

  return (
    <>
      {error && <div>Error: {error.message}</div>}
      <button onClick={handleAction} disabled={isLoading}>
        {isLoading ? 'Loading...' : 'Submit'}
      </button>
    </>
  )
}
```

### Keyboard Shortcuts

```tsx
import { useKeyboardShortcut } from '@/components'

function MyComponent() {
  useKeyboardShortcut('s', () => console.log('Save!'), {
    ctrl: true,
  })

  useKeyboardShortcut('Escape', () => closeModal())

  return <div>Press Ctrl+S to save</div>
}
```

### Click Outside

```tsx
import { useRef } from 'react'
import { useClickOutside } from '@/components'

function Dropdown() {
  const ref = useRef<HTMLDivElement>(null)
  const [isOpen, setIsOpen] = useState(false)

  useClickOutside(ref, () => setIsOpen(false))

  return (
    <div ref={ref}>
      <button onClick={() => setIsOpen(!isOpen)}>Toggle</button>
      {isOpen && <div>Dropdown content</div>}
    </div>
  )
}
```

---

## Testing

### Unit Testing with Jest + RTL

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { TranscriptInput } from '@/components'

describe('TranscriptInput', () => {
  it('renders with placeholder', () => {
    render(<TranscriptInput value="" onChange={() => {}} />)
    expect(screen.getByPlaceholderText('Enter transcript...')).toBeInTheDocument()
  })

  it('calls onChange when typing', () => {
    const onChange = jest.fn()
    render(<TranscriptInput value="" onChange={onChange} />)

    fireEvent.change(screen.getByRole('textbox'), {
      target: { value: 'Hello' },
    })

    expect(onChange).toHaveBeenCalledWith('Hello')
  })
})
```

---

## Troubleshooting

### Component not rendering?
- Ensure 'use client' directive at the top of the file
- Check that all dependencies are installed
- Verify the import path is correct

### Animations not working?
- Framer Motion requires 'use client'
- Check that AnimatePresence wraps animated components
- Verify transition props are correctly set

### TypeScript errors?
- Ensure types are imported from '@/types/api'
- Check that all required props are provided
- Verify Next.js and React versions are correct

### Styling issues?
- Verify globals.css is imported in layout
- Check Tailwind config includes component paths
- Ensure glassmorphic classes are defined

---

## Next Steps

1. Visit `/demo` to see all components in action
2. Read the full README.md for detailed documentation
3. Check the TypeScript types in `/types/api.ts`
4. Explore the API client in `/lib/api-client.ts`
5. Customize styles in `app/globals.css`

---

**Happy coding!** 🚀
