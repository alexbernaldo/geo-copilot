import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import DiagnosticoPage from './DiagnosticoPage'

export const routes: RouteObject[] = [{ path: 'diagnostico', element: createElement(DiagnosticoPage) }]
