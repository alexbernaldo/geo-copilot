import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import AsistentePage from './AsistentePage'

export const routes: RouteObject[] = [{ path: 'proyectos/nuevo', element: createElement(AsistentePage) }]
