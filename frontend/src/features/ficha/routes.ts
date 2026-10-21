import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import FichaPage from './FichaPage'

export const routes: RouteObject[] = [{ path: 'ficha', element: createElement(FichaPage) }]
