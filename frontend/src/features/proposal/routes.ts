import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import PropuestaPage from './PropuestaPage'

export const routes: RouteObject[] = [{ path: 'propuesta', element: createElement(PropuestaPage) }]
