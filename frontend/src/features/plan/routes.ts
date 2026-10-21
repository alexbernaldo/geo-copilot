import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import PlanPage from './PlanPage'

export const routes: RouteObject[] = [{ path: 'plan', element: createElement(PlanPage) }]
