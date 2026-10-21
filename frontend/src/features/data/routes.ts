import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import DatosdelestudioPage from './DatosdelestudioPage'

export const routes: RouteObject[] = [{ path: 'datos', element: createElement(DatosdelestudioPage) }]
