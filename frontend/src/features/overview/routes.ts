import { createElement } from 'react'
import type { RouteObject } from 'react-router-dom'
import ResumenPage from './ResumenPage'

export const routes: RouteObject[] = [{ index: true, element: createElement(ResumenPage) }]
