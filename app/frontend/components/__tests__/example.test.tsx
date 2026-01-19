/**
 * Example test suite for UI components
 *
 * To run these tests, install:
 * npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom
 *
 * Add to package.json:
 * "scripts": {
 *   "test": "jest",
 *   "test:watch": "jest --watch"
 * }
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AnalysisCard } from '../AnalysisCard'
import { TranscriptInput } from '../TranscriptInput'
import { FeedbackModal } from '../FeedbackModal'
import type { AnalysisResponse, EvaluationRequest } from '@/types/api'

// Mock Framer Motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    article: ({ children, ...props }: any) => <article {...props}>{children}</article>,
    p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
    button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
    section: ({ children, ...props }: any) => <section {...props}>{children}</section>,
  },
  AnimatePresence: ({ children }: any) => children,
}))

describe('AnalysisCard', () => {
  const mockAnalysis: AnalysisResponse = {
    id: 'test-123',
    summary: 'This is a test summary of the analysis.',
    next_actions: ['Action 1', 'Action 2', 'Action 3'],
    created_at: '2024-01-19T12:00:00Z',
    transcript: 'Test transcript',
    observability: {
      llm_provider: 'anthropic',
      llm_model: 'claude-3.5-sonnet',
      input_tokens: 1500,
      output_tokens: 300,
      latency_ms: 1200,
    },
  }

  it('renders analysis summary', () => {
    render(<AnalysisCard analysis={mockAnalysis} />)
    expect(screen.getByText(/This is a test summary/)).toBeInTheDocument()
  })

  it('displays all next actions as chips', () => {
    render(<AnalysisCard analysis={mockAnalysis} />)
    expect(screen.getByText('Action 1')).toBeInTheDocument()
    expect(screen.getByText('Action 2')).toBeInTheDocument()
    expect(screen.getByText('Action 3')).toBeInTheDocument()
  })

  it('shows observability metadata', () => {
    render(<AnalysisCard analysis={mockAnalysis} />)
    expect(screen.getByText('1200ms')).toBeInTheDocument()
    expect(screen.getByText('1800')).toBeInTheDocument() // Total tokens
  })

  it('calls onFeedback when feedback button is clicked', () => {
    const onFeedback = jest.fn()
    render(<AnalysisCard analysis={mockAnalysis} onFeedback={onFeedback} />)

    fireEvent.click(screen.getByText('Provide Feedback'))
    expect(onFeedback).toHaveBeenCalledWith('test-123')
  })

  it('expands summary when chevron is clicked', () => {
    render(<AnalysisCard analysis={mockAnalysis} />)

    const expandButton = screen.getByLabelText(/Expand summary/)
    fireEvent.click(expandButton)

    expect(screen.getByLabelText(/Collapse summary/)).toBeInTheDocument()
  })

  it('copies action text to clipboard', async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue(undefined),
      },
    })

    render(<AnalysisCard analysis={mockAnalysis} />)

    const actionButton = screen.getByText('Action 1')
    fireEvent.click(actionButton)

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Action 1')
    })
  })
})

describe('TranscriptInput', () => {
  it('renders with label and placeholder', () => {
    render(
      <TranscriptInput
        value=""
        onChange={() => {}}
        label="Test Label"
        placeholder="Test placeholder"
      />
    )

    expect(screen.getByLabelText('Test Label')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Test placeholder')).toBeInTheDocument()
  })

  it('calls onChange when text is entered', async () => {
    const onChange = jest.fn()
    const user = userEvent.setup()

    render(<TranscriptInput value="" onChange={onChange} />)

    const textarea = screen.getByRole('textbox')
    await user.type(textarea, 'Hello')

    expect(onChange).toHaveBeenCalled()
  })

  it('displays character count', () => {
    render(
      <TranscriptInput value="Hello world" onChange={() => {}} maxLength={1000} />
    )

    expect(screen.getByText(/11 \/ 1,000/)).toBeInTheDocument()
  })

  it('shows warning color when near limit', () => {
    render(
      <TranscriptInput
        value="A".repeat(950)}
        onChange={() => {}}
        maxLength={1000}
      />
    )

    const charCount = screen.getByText(/950 \/ 1,000/)
    expect(charCount).toHaveClass('text-yellow-400')
  })

  it('truncates text at maxLength', async () => {
    const onChange = jest.fn()
    const user = userEvent.setup()

    render(<TranscriptInput value="" onChange={onChange} maxLength={10} />)

    const textarea = screen.getByRole('textbox')
    await user.type(textarea, 'This is a very long text')

    // Should be called with truncated text
    const calls = onChange.mock.calls
    const lastCall = calls[calls.length - 1][0]
    expect(lastCall.length).toBeLessThanOrEqual(10)
  })

  it('pastes from clipboard', async () => {
    const onChange = jest.fn()

    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        readText: jest.fn().mockResolvedValue('Pasted text'),
      },
    })

    render(<TranscriptInput value="" onChange={onChange} />)

    const pasteButton = screen.getByLabelText('Paste from clipboard')
    fireEvent.click(pasteButton)

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('Pasted text')
    })
  })

  it('shows error message when provided', () => {
    render(<TranscriptInput value="" onChange={() => {}} error="Test error" />)

    expect(screen.getByText('Test error')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
  })

  it('disables input when loading', () => {
    render(<TranscriptInput value="" onChange={() => {}} isLoading={true} />)

    expect(screen.getByLabelText('Loading')).toBeInTheDocument()
  })
})

describe('FeedbackModal', () => {
  const mockOnSubmit = jest.fn().mockResolvedValue(undefined)
  const mockOnClose = jest.fn()

  beforeEach(() => {
    mockOnSubmit.mockClear()
    mockOnClose.mockClear()
  })

  it('does not render when closed', () => {
    render(
      <FeedbackModal
        isOpen={false}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        analysisId="test-123"
      />
    )

    expect(screen.queryByText('Provide Feedback')).not.toBeInTheDocument()
  })

  it('renders when open', () => {
    render(
      <FeedbackModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        analysisId="test-123"
      />
    )

    expect(screen.getByText('Provide Feedback')).toBeInTheDocument()
  })

  it('allows selecting star rating', () => {
    render(
      <FeedbackModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        analysisId="test-123"
      />
    )

    const fourStarButton = screen.getByLabelText('4 stars')
    fireEvent.click(fourStarButton)

    expect(fourStarButton).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByText('Very Good')).toBeInTheDocument()
  })

  it('shows error when submitting without rating', async () => {
    render(
      <FeedbackModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        analysisId="test-123"
      />
    )

    const submitButton = screen.getByText('Submit Feedback')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Please provide a rating')).toBeInTheDocument()
    })

    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  it('submits feedback with rating and comment', async () => {
    const user = userEvent.setup()

    render(
      <FeedbackModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        analysisId="test-123"
      />
    )

    // Select rating
    fireEvent.click(screen.getByLabelText('5 stars'))

    // Enter comment
    const commentBox = screen.getByPlaceholderText('Share your thoughts...')
    await user.type(commentBox, 'Great analysis!')

    // Submit
    fireEvent.click(screen.getByText('Submit Feedback'))

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        score: 5,
        is_hallucination: false,
        comment: 'Great analysis!',
      })
    })
  })

  it('handles hallucination checkbox', async () => {
    render(
      <FeedbackModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        analysisId="test-123"
      />
    )

    // Select rating
    fireEvent.click(screen.getByLabelText('3 stars'))

    // Check hallucination
    const hallucinationCheckbox = screen.getByRole('checkbox')
    fireEvent.click(hallucinationCheckbox)

    // Submit
    fireEvent.click(screen.getByText('Submit Feedback'))

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        score: 3,
        is_hallucination: true,
        comment: undefined,
      })
    })
  })

  it('closes modal on backdrop click', () => {
    render(
      <FeedbackModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={mockOnSubmit}
        analysisId="test-123"
      />
    )

    const backdrop = screen.getByRole('dialog').parentElement?.previousSibling
    if (backdrop) {
      fireEvent.click(backdrop as Element)
      expect(mockOnClose).toHaveBeenCalled()
    }
  })

  it('disables inputs while submitting', async () => {
    const slowSubmit = jest.fn(() => new Promise((resolve) => setTimeout(resolve, 1000)))

    render(
      <FeedbackModal
        isOpen={true}
        onClose={mockOnClose}
        onSubmit={slowSubmit}
        analysisId="test-123"
      />
    )

    // Select rating and submit
    fireEvent.click(screen.getByLabelText('4 stars'))
    fireEvent.click(screen.getByText('Submit Feedback'))

    // Check that button shows loading state
    await waitFor(() => {
      expect(screen.getByText('Submitting...')).toBeInTheDocument()
    })

    // Verify inputs are disabled
    expect(screen.getByRole('checkbox')).toBeDisabled()
    expect(screen.getByPlaceholderText('Share your thoughts...')).toBeDisabled()
  })
})

describe('Accessibility', () => {
  it('AnalysisCard has proper ARIA labels', () => {
    const mockAnalysis: AnalysisResponse = {
      id: 'test-123',
      summary: 'Test',
      next_actions: ['Action 1'],
      created_at: '2024-01-19T12:00:00Z',
      transcript: 'Test',
    }

    render(<AnalysisCard analysis={mockAnalysis} />)

    expect(screen.getByRole('article')).toHaveAttribute(
      'aria-label',
      expect.stringContaining('Analysis created at')
    )
  })

  it('TranscriptInput has help text', () => {
    render(<TranscriptInput value="" onChange={() => {}} id="test-input" />)

    expect(screen.getByRole('textbox')).toHaveAttribute(
      'aria-describedby',
      expect.stringContaining('help')
    )
  })

  it('FeedbackModal has dialog role', () => {
    render(
      <FeedbackModal
        isOpen={true}
        onClose={() => {}}
        onSubmit={async () => {}}
        analysisId="test-123"
      />
    )

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby')
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-describedby')
  })
})
