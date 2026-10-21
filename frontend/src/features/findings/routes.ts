import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import HallazgosPage from './HallazgosPage'

export const routes: RouteObject[] = [{ path: 'hallazgos', element: createElement(HallazgosPage) }]
