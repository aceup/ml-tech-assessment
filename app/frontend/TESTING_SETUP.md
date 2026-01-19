# Frontend Testing Setup Guide

Comprehensive guide for setting up and running tests for the Next.js frontend application.

## Table of Contents

- [Test Infrastructure](#test-infrastructure)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Test Configuration](#test-configuration)
- [Running Tests](#running-tests)
- [Coverage Reports](#coverage-reports)
- [Best Practices](#best-practices)

## Test Infrastructure

### Recommended Test Stack

| Purpose | Tool | Version | Reason |
|---------|------|---------|--------|
| **Test Runner** | Jest | 29.x+ | Built-in Next.js support, excellent TypeScript integration |
| **Component Testing** | React Testing Library | 14.x+ | Encourages testing user behavior, not implementation |
| **E2E Testing** | Playwright | 1.40.x+ | Fast, reliable, supports multiple browsers |
| **Mocking** | MSW (Mock Service Worker) | 2.x+ | Network request mocking without modifying code |
| **API Testing** | Supertest | 6.x+ | Test HTTP servers easily |
| **Coverage** | c8 | 8.x+ | Modern coverage tool for TypeScript |

### Project Structure

```
frontend/
├── __tests__/                    # Test files
│   ├── unit/                     # Unit tests
│   │   ├── components/
│   │   ├── lib/
│   │   └── utils/
│   ├── integration/              # Integration tests
│   │   └── api/
│   ├── e2e/                      # End-to-end tests
│   │   └── flows/
│   └── mocks/                    # Mock setup
│       ├── handlers.ts           # MSW handlers
│       └── server.ts             # MSW server
├── src/                          # Source code
├── app/                          # App Router pages
├── components/                   # React components
├── lib/                          # Utilities
├── jest.config.ts                # Jest configuration
├── playwright.config.ts          # Playwright configuration
└── vitest.config.ts              # Vitest configuration (optional)
```

## Unit Testing

Unit tests verify individual components and functions work correctly in isolation.

### Setup Jest for Next.js

**1. Install dependencies:**

```bash
npm install --save-dev \
  jest \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  jest-environment-jsdom \
  @types/jest
```

**2. Create jest.config.ts:**

```typescript
// jest.config.ts
import type { Config } from 'jest'
import nextJest from 'next/jest'

const createJestConfig = nextJest({
  dir: './',
})

const config: Config = {
  coverageProvider: 'v8',
  testEnvironment: 'jsdom',

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.ts'],

  // Module paths
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },

  // Test patterns
  testMatch: [
    '<rootDir>/__tests__/**/*.test.ts',
    '<rootDir>/__tests__/**/*.test.tsx',
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/.next/**',
  ],

  // Thresholds
  coverageThreshold: {
    global: {
      statements: 70,
      branches: 70,
      functions: 70,
      lines: 70,
    },
  },
}

export default createJestConfig(config)
```

**3. Create setup file:**

```typescript
// __tests__/setup.ts
import '@testing-library/jest-dom'

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_API_KEY = 'test-key'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
      pathname: '/',
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
}))
```

### Writing Unit Tests

**Example: Component Unit Test**

```typescript
// components/Button.tsx
import React from 'react'

interface ButtonProps {
  label: string
  onClick?: () => void
  disabled?: boolean
  variant?: 'primary' | 'secondary'
}

export function Button({
  label,
  onClick,
  disabled = false,
  variant = 'primary',
}: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
      aria-label={label}
    >
      {label}
    </button>
  )
}
```

```typescript
// __tests__/unit/components/Button.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '@/components/Button'

describe('Button Component', () => {
  describe('Rendering', () => {
    it('should render with label', () => {
      render(<Button label="Click me" />)
      expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
    })

    it('should apply correct variant class', () => {
      const { container } = render(
        <Button label="Primary" variant="primary" />
      )
      expect(container.querySelector('.btn-primary')).toBeInTheDocument()
    })
  })

  describe('Interactions', () => {
    it('should call onClick handler when clicked', async () => {
      const handleClick = jest.fn()
      render(<Button label="Click" onClick={handleClick} />)

      const button = screen.getByRole('button')
      await userEvent.click(button)

      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('should not call onClick when disabled', async () => {
      const handleClick = jest.fn()
      render(<Button label="Click" onClick={handleClick} disabled />)

      const button = screen.getByRole('button')
      await userEvent.click(button)

      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper aria-label', () => {
      render(<Button label="Submit form" />)
      expect(screen.getByLabelText('Submit form')).toBeInTheDocument()
    })

    it('should be disabled when disabled prop is true', () => {
      render(<Button label="Click" disabled />)
      expect(screen.getByRole('button')).toBeDisabled()
    })
  })
})
```

**Example: Utility Function Test**

```typescript
// lib/utils.ts
export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date)
}

export function calculateAge(birthDate: Date): number {
  const today = new Date()
  let age = today.getFullYear() - birthDate.getFullYear()
  const monthDiff = today.getMonth() - birthDate.getMonth()
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--
  }
  return age
}
```

```typescript
// __tests__/unit/lib/utils.test.ts
import { formatDate, calculateAge } from '@/lib/utils'

describe('Utility Functions', () => {
  describe('formatDate', () => {
    it('should format date correctly', () => {
      const date = new Date('2025-01-19')
      const result = formatDate(date)
      expect(result).toMatch(/January 19, 2025/)
    })

    it('should handle different dates', () => {
      const date = new Date('2024-12-25')
      expect(formatDate(date)).toContain('December')
    })
  })

  describe('calculateAge', () => {
    it('should calculate age correctly', () => {
      const birthDate = new Date('2000-01-19')
      const age = calculateAge(birthDate)
      expect(age).toBeGreaterThanOrEqual(25)
    })

    it('should handle edge case: birthday not yet this year', () => {
      const today = new Date()
      const futureMonth = new Date(today.getFullYear(), today.getMonth() + 1, 1)
      const birthDate = new Date(today.getFullYear() - 30, futureMonth.getMonth(), 1)

      expect(calculateAge(birthDate)).toBe(29)
    })
  })
})
```

## Integration Testing

Integration tests verify multiple components work together correctly.

### Setup MSW (Mock Service Worker)

```typescript
// __tests__/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  // Health check
  http.get('http://localhost:8000/api/health', () => {
    return HttpResponse.json({ status: 'ok' })
  }),

  // Transcripts API
  http.get('http://localhost:8000/api/v1/transcripts', () => {
    return HttpResponse.json({
      items: [
        { id: '1', title: 'Test Transcript', content: 'Test content' },
      ],
      total: 1,
    })
  }),

  http.post('http://localhost:8000/api/v1/transcripts', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json(
      { id: '2', ...body },
      { status: 201 }
    )
  }),
]
```

```typescript
// __tests__/mocks/server.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)

// Enable API mocking before running tests
beforeAll(() => server.listen())

// Reset handlers after each test
afterEach(() => server.resetHandlers())

// Disable API mocking after tests are done
afterAll(() => server.close())
```

### Integration Test Example

```typescript
// __tests__/integration/api/transcripts.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TranscriptList } from '@/components/TranscriptList'
import { server } from '@/__tests__/mocks/server'
import { HttpResponse, http } from 'msw'

describe('Transcripts API Integration', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })
  })

  function renderWithProviders(component: React.ReactNode) {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    )
  }

  it('should fetch and display transcripts', async () => {
    renderWithProviders(<TranscriptList />)

    await waitFor(() => {
      expect(screen.getByText('Test Transcript')).toBeInTheDocument()
    })
  })

  it('should handle API errors gracefully', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/transcripts', () => {
        return HttpResponse.json(
          { error: 'Internal Server Error' },
          { status: 500 }
        )
      })
    )

    renderWithProviders(<TranscriptList />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('should retry on network error', async () => {
    let attempts = 0

    server.use(
      http.get('http://localhost:8000/api/v1/transcripts', () => {
        attempts++
        if (attempts === 1) {
          return HttpResponse.error()
        }
        return HttpResponse.json({ items: [] })
      })
    )

    renderWithProviders(<TranscriptList />)

    await waitFor(() => {
      expect(attempts).toBeGreaterThan(1)
    })
  })
})
```

## End-to-End Testing

E2E tests verify complete user workflows from the UI perspective.

### Setup Playwright

**1. Install Playwright:**

```bash
npm install --save-dev \
  @playwright/test \
  @playwright/experimental-ct-react
```

**2. Create playwright.config.ts:**

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './__tests__/e2e',
  testMatch: '**/*.spec.ts',

  // Run tests in serial
  fullyParallel: false,

  // Fail on console errors
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  // Test timeout
  timeout: 30 * 1000,

  // Expect timeout
  expect: {
    timeout: 5000,
  },

  // Browsers to test
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  // Web server configuration
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### E2E Test Example

```typescript
// __tests__/e2e/flows/upload-transcript.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Upload Transcript Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to app before each test
    await page.goto('/')

    // Wait for app to be ready
    await page.waitForLoadState('networkidle')
  })

  test('should upload a transcript successfully', async ({ page }) => {
    // 1. Click upload button
    await page.click('button:has-text("Upload Transcript")')

    // 2. Fill form
    await page.fill('input[name="title"]', 'Test Transcript')
    await page.fill('textarea[name="content"]', 'Test content here')

    // 3. Submit form
    await page.click('button[type="submit"]')

    // 4. Verify success message
    await expect(page.locator('text=Upload successful')).toBeVisible()

    // 5. Verify navigation
    await expect(page).toHaveURL(/\/transcripts\/\d+/)
  })

  test('should show validation errors for empty fields', async ({ page }) => {
    // 1. Click upload button
    await page.click('button:has-text("Upload Transcript")')

    // 2. Try to submit without filling form
    await page.click('button[type="submit"]')

    // 3. Verify error messages
    await expect(page.locator('text=Title is required')).toBeVisible()
    await expect(page.locator('text=Content is required')).toBeVisible()
  })

  test('should display uploaded transcript', async ({ page }) => {
    // 1. Upload a transcript
    await page.click('button:has-text("Upload Transcript")')
    await page.fill('input[name="title"]', 'My Transcript')
    await page.fill('textarea[name="content"]', 'Content')
    await page.click('button[type="submit"]')

    // 2. Navigate to detail page
    await page.waitForURL(/\/transcripts\/\d+/)

    // 3. Verify transcript data is displayed
    await expect(page.locator('h1:has-text("My Transcript")')).toBeVisible()
    await expect(page.locator('text=Content')).toBeVisible()
  })

  test('should handle network errors gracefully', async ({ page }) => {
    // 1. Simulate network error
    await page.context().setOffline(true)

    // 2. Try to upload
    await page.click('button:has-text("Upload Transcript")')
    await page.fill('input[name="title"]', 'Test')
    await page.fill('textarea[name="content"]', 'Test')
    await page.click('button[type="submit"]')

    // 3. Verify error message
    await expect(page.locator('text=Network error')).toBeVisible()

    // 4. Restore connection
    await page.context().setOffline(false)

    // 5. Retry should work
    await page.click('button:has-text("Retry")')
    await expect(page.locator('text=Upload successful')).toBeVisible()
  })
})
```

## Test Configuration

### Update package.json

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:unit": "jest __tests__/unit",
    "test:integration": "jest __tests__/integration",
    "test:e2e": "playwright test",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

### .gitignore additions

```
# Test coverage
coverage/
.nyc_output/

# Playwright
test-results/
playwright-report/

# Jest
.jest-cache/
```

## Running Tests

### Unit Tests

```bash
# Run all unit tests
npm run test:unit

# Watch mode for development
npm run test:watch

# Run specific test file
npm test -- Button.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="should render"

# Run with coverage
npm run test:coverage
```

### Integration Tests

```bash
# Run all integration tests
npm run test:integration

# Run specific integration test
npm test -- transcripts.test.tsx

# Run with detailed output
npm test -- --verbose
```

### E2E Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run specific test file
npm run test:e2e -- upload-transcript.spec.ts

# Run in UI mode (recommended for development)
npm run test:e2e:ui

# Run in debug mode
npm run test:e2e:debug

# Run in headed mode (see browser)
npm run test:e2e -- --headed

# Run single test
npm run test:e2e -- --grep "should upload"

# Generate HTML report
npm run test:e2e
npx playwright show-report
```

## Coverage Reports

### Generate Coverage

```bash
# Generate coverage report
npm run test:coverage

# View coverage in browser
open coverage/lcov-report/index.html
```

### Coverage Thresholds

Configure in jest.config.ts:

```typescript
coverageThreshold: {
  global: {
    statements: 70,
    branches: 70,
    functions: 70,
    lines: 70,
  },
  './components/': {
    statements: 80,
    branches: 75,
    functions: 80,
    lines: 80,
  },
}
```

## Best Practices

### 1. Test Naming

```typescript
// Bad: Unclear what is being tested
it('works', () => {})

// Good: Clear description of behavior
it('should display error message when API returns 500 status', () => {})

describe('Button Component', () => {
  describe('Rendering', () => {
    it('should render with label text')
  })

  describe('Interactions', () => {
    it('should call onClick handler when clicked')
  })
})
```

### 2. Arrange-Act-Assert Pattern

```typescript
it('should update transcript title', async () => {
  // Arrange: Setup test data and state
  const mockTranscript = { id: '1', title: 'Old Title' }
  render(<TranscriptEditor transcript={mockTranscript} />)

  // Act: Perform the action
  const input = screen.getByDisplayValue('Old Title')
  await userEvent.clear(input)
  await userEvent.type(input, 'New Title')
  await userEvent.click(screen.getByRole('button', { name: /save/i }))

  // Assert: Verify the outcome
  expect(mockOnSave).toHaveBeenCalledWith({ id: '1', title: 'New Title' })
})
```

### 3. Avoid Testing Implementation Details

```typescript
// Bad: Testing implementation details
it('should set state', () => {
  const { result } = renderHook(() => useTranscript())
  expect(result.current.state).toBe('loading')
})

// Good: Testing user-facing behavior
it('should display loading message while fetching', async () => {
  render(<TranscriptDetail id="1" />)
  expect(screen.getByText('Loading...')).toBeInTheDocument()
  await waitFor(() => {
    expect(screen.getByText('Transcript content')).toBeInTheDocument()
  })
})
```

### 4. Mock External Dependencies

```typescript
// Mock API calls
jest.mock('@/lib/api', () => ({
  fetchTranscript: jest.fn(),
}))

// Use in tests
import { fetchTranscript } from '@/lib/api'

beforeEach(() => {
  ;(fetchTranscript as jest.Mock).mockResolvedValue({
    id: '1',
    title: 'Test',
  })
})
```

### 5. Keep Tests Isolated

```typescript
// Each test should be independent
describe('TranscriptList', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    // Fresh state for each test
    queryClient = new QueryClient()
    server.resetHandlers()
  })

  it('test 1', () => {
    // No dependencies on other tests
  })

  it('test 2', () => {
    // Can run in any order
  })
})
```

### 6. Use Test Data Builders

```typescript
// factory.ts
export function createTranscript(overrides?: Partial<Transcript>): Transcript {
  return {
    id: '1',
    title: 'Test Transcript',
    content: 'Test content',
    createdAt: new Date(),
    ...overrides,
  }
}

// In tests
const transcript = createTranscript({ title: 'Custom Title' })
```

### 7. Test User Interactions, Not DOM

```typescript
// Bad: Testing implementation
it('should add to list', () => {
  render(<List />)
  expect(document.querySelectorAll('li').length).toBe(1)
})

// Good: Testing user behavior
it('should display new item when user adds it', async () => {
  render(<List />)
  await userEvent.type(screen.getByPlaceholderText('Enter item'), 'New item')
  await userEvent.click(screen.getByRole('button', { name: /add/i }))
  expect(screen.getByText('New item')).toBeInTheDocument()
})
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

---

**Version:** 1.0.0
**Last Updated:** 2025-01-19
