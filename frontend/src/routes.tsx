import { createElement } from 'react'
import { createBrowserRouter, Outlet, type RouteObject } from 'react-router-dom'
import { routes as overview } from './features/overview/routes'
import { routes as ficha } from './features/ficha/routes'
import { routes as data } from './features/data/routes'
import { routes as competition } from './features/competition/routes'
import { routes as diagnosis } from './features/diagnosis/routes'
import { routes as findings } from './features/findings/routes'
import { routes as plan } from './features/plan/routes'
import { routes as proposal } from './features/proposal/routes'
import { routes as quality } from './features/quality/routes'
import { routes as projects } from './features/projects/routes'
import { routes as wizard } from './features/wizard/routes'
import { routes as settings } from './features/settings/routes'
import { Shell } from './components/Shell'
import KitPage from './KitPage'

/** El shell (navegación global y de proyecto) envuelve todas las rutas. E y F aportan sus rutas desde features/<x>/routes.ts. */
const projectRoutes: RouteObject[] = [...overview, ...ficha, ...data, ...competition, ...diagnosis, ...findings, ...plan, ...proposal, ...quality]

export const routes: RouteObject[] = [
  {
    element: createElement(Shell),
    children: [
      ...projects,
      ...wizard,
      ...settings,
      ...(import.meta.env.DEV ? [{ path: '_kit', element: createElement(KitPage) }] : []),
      { path: 'proyectos/:id', element: createElement(Outlet), children: projectRoutes },
    ],
  },
]

export const router = createBrowserRouter(routes)
