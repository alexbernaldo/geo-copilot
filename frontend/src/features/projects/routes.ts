import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import ProyectosPage from './ProyectosPage'

export const routes: RouteObject[] = [{ index: true, element: createElement(ProyectosPage) }]
