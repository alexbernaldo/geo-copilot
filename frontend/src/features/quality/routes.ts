import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import CalidadytrazasPage from './CalidadytrazasPage'

export const routes: RouteObject[] = [{ path: 'calidad', element: createElement(CalidadytrazasPage) }]
