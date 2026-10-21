import { useState } from 'react'
import { Link, NavLink, Outlet, useMatch } from 'react-router-dom'
import { BarChart3, ClipboardList, Database, FileCheck2, Gauge, Lightbulb, ListChecks, Moon, ShieldCheck, Sun, Users } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useProgress, useProject, useSettings } from '@/api/hooks'
import { useTheme } from '@/lib/theme'
import { Avatar, Chip, Logo, type Tone } from './display'
import { Button, Drawer } from './primitives'
import { ProgressPanel, useLiveProgress } from './ProgressPanel'

type Section = { to: string; label: string; icon: LucideIcon; end?: boolean; checkpoint?: 'ficha' | 'competencia' | 'hallazgos' | 'plan' }

const GROUPS: { label: string; items: Section[] }[] = [
  {
    label: 'Revisión',
    items: [
      { to: '', label: 'Resumen', icon: Gauge, end: true },
      { to: 'ficha', label: 'Ficha', icon: ClipboardList, checkpoint: 'ficha' },
      { to: 'datos', label: 'Datos del estudio', icon: Database },
      { to: 'competencia', label: 'Competencia', icon: Users, checkpoint: 'competencia' },
    ],
  },
  {
    label: 'Resultados',
    items: [
      { to: 'diagnostico', label: 'Diagnóstico', icon: BarChart3 },
      { to: 'hallazgos', label: 'Hallazgos', icon: Lightbulb, checkpoint: 'hallazgos' },
      { to: 'plan', label: 'Plan', icon: ListChecks, checkpoint: 'plan' },
      { to: 'propuesta', label: 'Propuesta', icon: FileCheck2 },
      { to: 'calidad', label: 'Calidad y trazas', icon: ShieldCheck },
    ],
  },
]

const ESTADO_PROYECTO: Record<string, { tone: Tone; texto: string }> = {
  borrador: { tone: 'neutral', texto: 'Borrador' },
  listo_para_lanzar: { tone: 'neutral', texto: 'Listo para lanzar' },
  en_ejecucion: { tone: 'info', texto: 'En ejecución' },
  esperando_revision: { tone: 'warn', texto: 'Esperando revisión' },
  completado: { tone: 'good', texto: 'Completado' },
  error: { tone: 'bad', texto: 'Con error' },
  interrumpido: { tone: 'warn', texto: 'Interrumpido' },
}

const ICON = { size: 17, strokeWidth: 1.75, 'aria-hidden': true } as const

function ThemeToggle() {
  const { resolved, setChoice } = useTheme()
  const next = resolved === 'dark' ? 'light' : 'dark'
  return (
    <Button variant="ghost" size="sm" aria-label={resolved === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'} onClick={() => setChoice(next)}>
      {resolved === 'dark' ? <Sun size={16} strokeWidth={1.75} aria-hidden /> : <Moon size={16} strokeWidth={1.75} aria-hidden />}
    </Button>
  )
}

/** Estado de la conexión: solo lee GET /settings, sin llamadas de red a OpenRouter. */
function ConnectionStatus() {
  const { data } = useSettings()
  if (!data) return null
  return (
    <Link to="/ajustes" style={{ textDecoration: 'none' }} aria-label={data.clave_configurada ? 'OpenRouter conectado' : 'OpenRouter sin configurar'}>
      <Chip tone={data.clave_configurada ? 'good' : 'warn'} dot>{data.clave_configurada ? 'OpenRouter configurado' : 'OpenRouter sin configurar'}</Chip>
    </Link>
  )
}

function RunIndicator({ projectId }: { projectId: string }) {
  const [open, setOpen] = useState(false)
  useLiveProgress(projectId)
  const { data } = useProgress(projectId)
  const running = data?.estado === 'en_ejecucion'
  const label = running ? `En ejecución${data?.contador ? `: ${data.contador.hechos} de ${data.contador.total}` : ''}` : data?.estado === 'esperando_revision' ? 'Esperando revisión' : 'Progreso'
  return (
    <>
      <Button size="sm" onClick={() => setOpen(true)}>
        {running && <span className="spinner" aria-hidden />}
        {label}
      </Button>
      <Drawer open={open} onOpenChange={setOpen} title="Progreso del análisis" description="Pasos, tiempo y coste acumulado del proyecto.">
        <ProgressPanel projectId={projectId} />
      </Drawer>
    </>
  )
}

function ProjectSidebar({ id }: { id: string }) {
  const { data: project } = useProject(id)
  const estado = project ? ESTADO_PROYECTO[project.estado] : undefined
  const nombre = project?.nombre ?? 'Proyecto'
  return (
    <nav className="sidenav" aria-label="Secciones del proyecto">
      <div className="side-project">
        <Avatar nombre={project?.marca ?? nombre} />
        <b>{nombre}</b>
        {estado && <span><Chip tone={estado.tone} dot>{estado.texto}</Chip></span>}
      </div>
      {GROUPS.map((g) => (
        <div key={g.label} role="group" aria-label={g.label}>
          <div className="side-label" aria-hidden>{g.label}</div>
          {g.items.map((s) => {
            const approved = s.checkpoint && project ? project.checkpoints[s.checkpoint] : undefined
            const Icon = s.icon
            return (
              <NavLink key={s.label} to={s.to === '' ? `/proyectos/${id}` : `/proyectos/${id}/${s.to}`} end={s.end} className="navlink" title={s.label}>
                <Icon {...ICON} />
                <span className="navlabel">{s.label}</span>
                {s.checkpoint && project && (
                  <span className="chip-dot" style={{ color: approved ? 'var(--good)' : 'var(--warn)' }} role="img" aria-label={approved ? 'Punto de control aprobado' : 'Punto de control pendiente'} />
                )}
              </NavLink>
            )
          })}
        </div>
      ))}
    </nav>
  )
}

/** Navegación global (Proyectos, Ajustes) y del proyecto (las 9 secciones de A3). */
export function Shell() {
  const match = useMatch('/proyectos/:id/*')
  const projectId = match?.params.id && match.params.id !== 'nuevo' ? match.params.id : null
  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brandmark" aria-label="Preload, ir a proyectos">
          <Logo />
          <span>Preload <small>visibilidad en IA</small></span>
        </Link>
        <nav className="topnav" aria-label="Navegación global">
          <NavLink to="/" end className="navlink">Proyectos</NavLink>
          <NavLink to="/ajustes" className="navlink">Ajustes</NavLink>
        </nav>
        <div className="topbar-end">
          {projectId && <RunIndicator projectId={projectId} />}
          <ConnectionStatus />
          <ThemeToggle />
        </div>
      </header>
      <div className="shell-body" data-project={projectId ? 'true' : undefined}>
        {projectId && <ProjectSidebar id={projectId} />}
        <main className="main" id="contenido"><Outlet /></main>
      </div>
    </div>
  )
}
