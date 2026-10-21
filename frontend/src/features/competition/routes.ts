import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import CompetenciaPage from './CompetenciaPage'

export const routes: RouteObject[] = [{ path: 'competencia', element: createElement(CompetenciaPage) }]
