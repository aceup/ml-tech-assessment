# Frontend - Medical Transcript Analyzer

A modern Next.js web application for analyzing medical transcripts with AI-powered insights. Built with React 19, TypeScript, Tailwind CSS, and TanStack Query for robust data management.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Development](#development)
- [Docker Deployment](#docker-deployment)
- [Component Structure](#component-structure)
- [API Integration](#api-integration)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Framework** | Next.js | 16.1.3 |
| **Runtime** | Node.js | 20-alpine |
| **UI Library** | React | 19.2.3 |
| **Language** | TypeScript | 5.x |
| **Styling** | Tailwind CSS | 4.x |
| **State Management** | TanStack Query | 5.62.13 |
| **Animations** | Framer Motion | 11.15.0 |
| **Icons** | Lucide React | 0.469.0 |
| **Charts** | Recharts | 2.15.0 |

### Build Strategy

The Dockerfile uses a **multi-stage build** approach for optimal image size and security:

```
Stage 1: deps
  └─ Install npm dependencies

Stage 2: builder
  └─ Build Next.js application
     └─ Output: .next/standalone, .next/static, public

Stage 3: runner
  └─ Create minimal production image
     └─ Non-root user (nextjs:nodejs)
     └─ Health checks enabled
```

**Benefits:**
- Smaller final image (no build dependencies)
- Improved security (non-root user)
- Fast deployments (reuse deps layer)
- Health check monitoring

### Data Flow

```
Frontend (Next.js 3000)
    ↓
TanStack Query (data fetching/caching)
    ↓
API Routes (http://app:8000)
    ↓
Backend (Python FastAPI)
    ↓
Redis Cache
```

## Quick Start

### Prerequisites

- Node.js 20.x or higher
- npm 9.x or higher
- Docker & Docker Compose (for containerized deployment)

### Local Development

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your backend API URL
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   ```
   http://localhost:3000
   ```

### Docker Deployment

1. **Build image:**
   ```bash
   docker build -t transcript-analysis-frontend:latest ./frontend
   ```

2. **Run container:**
   ```bash
   docker run -p 3000:3000 \
     -e NEXT_PUBLIC_API_URL=http://app:8000 \
     -e NODE_ENV=production \
     transcript-analysis-frontend:latest
   ```

3. **Using Docker Compose:**
   ```bash
   # Production
   docker-compose up -d frontend

   # Development with hot reload
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d frontend
   ```

## Environment Configuration

### Environment Variables

The frontend requires these environment variables to function correctly:

| Variable | Purpose | Example | Required |
|----------|---------|---------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://app:8000` | Yes |
| `NEXT_PUBLIC_API_KEY` | API authentication key | `sk-xxx...` | Yes |
| `NODE_ENV` | Environment mode | `production` or `development` | No |
| `PORT` | Server port (Docker) | `3000` | No |
| `HOSTNAME` | Server hostname (Docker) | `0.0.0.0` | No |

### Development Configuration (.env.local)

```bash
# Backend API Configuration
# For local development: use localhost
# For Docker: use service name 'app'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your-api-key-here
NODE_ENV=development
```

### Production Configuration

```bash
# Docker environment
NEXT_PUBLIC_API_URL=http://app:8000
NEXT_PUBLIC_API_KEY=${API_KEY}  # Load from .env file
NODE_ENV=production
PORT=3000
HOSTNAME=0.0.0.0
```

### Environment Loading

Next.js automatically loads variables with the `NEXT_PUBLIC_` prefix on the client side:

```typescript
// Safe to use in client components
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
const apiKey = process.env.NEXT_PUBLIC_API_KEY;
```

Note: Variables without `NEXT_PUBLIC_` prefix are server-side only.

## Development

### Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

### Development Modes

#### Local Development (No Docker)

**Fastest iteration, best for component development:**

```bash
# 1. Start backend (separate terminal)
cd ..
python -m app.main

# 2. Start frontend dev server
cd frontend
npm run dev

# 3. Access http://localhost:3000
```

**Advantages:**
- Hot module reload (HMR) for instant feedback
- Full source maps for debugging
- Direct access to browser DevTools

#### Development with Docker Compose

**Integrated testing with backend:**

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Key differences from production:**
- Volume mounts for live code reload
- Development environment variables
- Extended startup period for initialization
- Exposed debug ports

### Code Structure

```
frontend/
├── app/                          # Next.js app directory (App Router)
│   ├── api/
│   │   └── health/route.ts       # Health check endpoint
│   ├── layout.tsx                # Root layout with providers
│   ├── page.tsx                  # Home page
│   └── globals.css               # Global styles
├── components/
│   ├── providers.tsx             # Client-side providers (Query, etc)
│   └── [other components]        # React components
├── lib/                          # Utility functions
│   ├── api.ts                    # API client
│   └── utils.ts                  # Helper functions
├── types/                        # TypeScript types
│   └── index.ts                  # Type definitions
├── public/                       # Static assets
├── Dockerfile                    # Production multi-stage build
├── next.config.ts                # Next.js configuration
├── tsconfig.json                 # TypeScript configuration
├── tailwind.config.ts            # Tailwind CSS configuration
└── package.json                  # Dependencies
```

### Development Workflow

1. **Create components in `components/`:**
   ```typescript
   // components/MyComponent.tsx
   'use client'

   import { useState } from 'react'

   export function MyComponent() {
     const [state, setState] = useState('')
     return <div>{state}</div>
   }
   ```

2. **Use in pages or other components:**
   ```typescript
   import { MyComponent } from '@/components/MyComponent'

   export default function Page() {
     return <MyComponent />
   }
   ```

3. **API integration with TanStack Query:**
   ```typescript
   import { useQuery } from '@tanstack/react-query'

   export function useTranscript(id: string) {
     return useQuery({
       queryKey: ['transcript', id],
       queryFn: async () => {
         const response = await fetch(
           `${process.env.NEXT_PUBLIC_API_URL}/transcripts/${id}`,
           {
             headers: {
               'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`
             }
           }
         )
         if (!response.ok) throw new Error('Failed to fetch')
         return response.json()
       }
     })
   }
   ```

## Docker Deployment

### Production Dockerfile

The Dockerfile is optimized for production deployments:

```dockerfile
# Stage 1: Dependencies (node:20-alpine)
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build

# Stage 3: Runner (minimal image)
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"
CMD ["node", "server.js"]
```

### Build & Run

**Build the image:**
```bash
docker build -t transcript-analysis-frontend:latest ./frontend
```

**Run as standalone container:**
```bash
docker run -d \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://backend:8000 \
  -e NEXT_PUBLIC_API_KEY=your-api-key \
  -e NODE_ENV=production \
  --name frontend \
  --restart unless-stopped \
  transcript-analysis-frontend:latest
```

**Run with Docker Compose:**
```bash
# Production
docker-compose up -d frontend

# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up frontend
```

### Health Check

The container includes a built-in health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"
```

This endpoint:
- Runs every 30 seconds
- Returns HTTP 200 if healthy
- Waits 5 seconds before first check
- Marks unhealthy after 3 failed attempts

**Check health status:**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Resource Limits

Docker Compose restricts resource usage:

```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'      # Max 50% of one CPU
      memory: 256M     # Max 256MB RAM
    reservations:
      cpus: '0.1'      # Reserve 10% CPU
      memory: 64M      # Reserve 64MB RAM
```

Adjust these based on your infrastructure:
- **Small deployments:** 256MB-512MB memory
- **Medium deployments:** 512MB-1GB memory
- **High traffic:** 1GB+ memory

## Component Structure

### Layout & Providers

**app/layout.tsx** - Root layout with global providers:
- Metadata configuration
- Font optimization (Inter, Playfair Display)
- Dark mode setup
- Provider wrapper (TanStack Query, etc)

**components/providers.tsx** - Client-side providers:
- QueryClientProvider for data fetching
- Other providers (context, theme, etc)

### Pages & Routes

```
app/
├── page.tsx                 # / (Home)
├── api/
│   └── health/route.ts     # GET /api/health (health check)
└── [dynamic routes]        # Future routes
```

### Styling

- **Framework:** Tailwind CSS 4.x
- **Utilities:** clsx, tailwind-merge, class-variance-authority
- **Global styles:** app/globals.css
- **Dark mode:** Configured by default

## API Integration

### API Client Setup

The frontend communicates with the backend API at `http://app:8000`:

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL
const API_KEY = process.env.NEXT_PUBLIC_API_KEY

async function apiCall(endpoint: string, options?: RequestInit) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return response.json()
}
```

### TanStack Query Setup

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,        // 5 minutes
      gcTime: 1000 * 60 * 10,           // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

### Example API Usage

```typescript
'use client'

import { useQuery } from '@tanstack/react-query'
import { apiCall } from '@/lib/api'

export function TranscriptList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['transcripts'],
    queryFn: () => apiCall('/api/v1/transcripts'),
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <ul>
      {data?.items.map((item: any) => (
        <li key={item.id}>{item.title}</li>
      ))}
    </ul>
  )
}
```

## Performance Optimization

### Built-in Optimizations

1. **Next.js Standalone Output**
   - Reduces bundle size by 50%
   - Faster deployments
   - Minimal dependencies

2. **Image Optimization**
   - Automatic WebP conversion
   - Responsive image serving
   - Built-in lazy loading

3. **Font Optimization**
   - Google Fonts with `next/font`
   - Automatic subsetting
   - CSS-in-JS for critical fonts

4. **CSS Optimization**
   - Tailwind CSS purging
   - Critical CSS extraction
   - Automatic minification

### Production Build Analysis

```bash
# Analyze bundle size
npm install -g @next/bundle-analyzer

# Then use in next.config.ts
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})
```

### Caching Strategy

**HTTP Caching:**
- Static assets: 1 year (immutable)
- HTML pages: No cache (revalidate)
- API responses: 5-30 minutes (via TanStack Query)

**Browser Caching:**
- Service Worker: Not enabled by default
- LocalStorage: Client-side state persistence
- IndexedDB: Large dataset caching

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>

# Or use different port
PORT=3001 npm run dev
```

#### API Connection Failed

**Symptoms:** "Cannot POST /api/v1/transcripts" errors

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/api/v1/health`
2. Check environment variables: `echo $NEXT_PUBLIC_API_URL`
3. For Docker: Use service name `app` instead of `localhost`

```bash
# Local development
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

# Docker Compose
NEXT_PUBLIC_API_URL=http://app:8000 npm run dev
```

#### Build Fails with TypeScript Errors

```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Rebuild
npm run build
```

#### Container Health Check Failing

```bash
# Check container logs
docker logs <container_name>

# Manual health check
docker exec <container_name> node -e "require('http').get('http://localhost:3000/api/health', (r) => console.log(r.statusCode))"

# Check service dependencies
docker-compose ps
```

#### Hot Reload Not Working in Docker

```bash
# Use development Docker Compose file
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Verify volume mounts
docker inspect <container_name> | grep -A 5 Mounts
```

### Debug Mode

**Enable verbose logging:**

```bash
# Development
DEBUG=* npm run dev

# Docker
docker run -e DEBUG=* transcript-analysis-frontend
```

**Browser DevTools:**
1. Open http://localhost:3000
2. Press F12 or Cmd+Option+I
3. Go to Network tab to monitor API calls
4. Check Console for errors

### Performance Debugging

**Analyze page performance:**

```typescript
// pages/debug.tsx
import { useEffect } from 'react'

export default function DebugPage() {
  useEffect(() => {
    const metrics = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    console.table({
      'DNS Lookup': `${metrics.domainLookupEnd - metrics.domainLookupStart}ms`,
      'TCP Connection': `${metrics.connectEnd - metrics.connectStart}ms`,
      'TTFB': `${metrics.responseStart - metrics.requestStart}ms`,
      'DOM Interactive': `${metrics.domInteractive - metrics.fetchStart}ms`,
      'Page Load': `${metrics.loadEventEnd - metrics.fetchStart}ms`,
    })
  }, [])

  return <div>Check console for performance metrics</div>
}
```

### Getting Help

1. **Check Next.js docs:** https://nextjs.org/docs
2. **React documentation:** https://react.dev
3. **TanStack Query:** https://tanstack.com/query/latest
4. **Issue tracker:** Check project GitHub issues

---

**Last Updated:** 2025-01-19
**Version:** 1.0.0
