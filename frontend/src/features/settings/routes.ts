import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import AjustesPage from './AjustesPage'

export const routes: RouteObject[] = [{ path: 'ajustes', element: createElement(AjustesPage) }]
