import type { ReactElement } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

/** MSW registra el manejador SSE al importar los handlers y exige `EventSource`; jsdom no lo trae. Este módulo debe importarse el primero. */
if (!('EventSource' in globalThis)) {
  class EventSourceStub { close(): void {} addEventListener(): void {} }
  ;(globalThis as unknown as { EventSource: unknown }).EventSource = EventSourceStub
}

if (!('ResizeObserver' in globalThis)) {
  class ResizeObserverStub { observe(): void {} unobserve(): void {} disconnect(): void {} }
  ;(globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver = ResizeObserverStub
}

/**
 * En Node, `Request` exige URL absolutas y el cliente generado usa `/api`.
 * Cada test lo sustituye con `vi.mock('@/api/client', apiClientMock)` por uno que apunta al origen de jsdom.
 */
export async function apiClientMock() {
  const { default: createClient } = await import('openapi-fetch')
  // `fetch` se resuelve en cada llamada: MSW parchea el global al arrancar el servidor, después de crear el cliente.
  return { api: createClient({ baseUrl: `${window.location.origin}/api`, fetch: (r: Request) => globalThis.fetch(r) }) }
}

export function renderRoute(ui: ReactElement, path: string, pattern: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes><Route path={pattern} element={ui} /></Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** ECharts necesita canvas, que jsdom no tiene: el gráfico se sustituye por un doble inerte. */
export const echartsStub = {
  init: () => ({ setOption: () => undefined, resize: () => undefined, dispose: () => undefined }),
  registerTheme: () => undefined,
}
