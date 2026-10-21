import { useState } from 'react'
import { Link, NavLink, Outlet, useMatch } from 'react-router-dom'
import { Moon, Sun } from 'lucide-react'
import { useProgress, useProject, useSettings } from '@/api/hooks'
import { useTheme } from '@/lib/theme'
import { Chip, type Tone } from './display'
import { Button, Drawer } from './primitives'
import { ProgressPanel } from './ProgressPanel'

const SECTIONS: { to: string; label: string; end?: boolean; checkpoint?: 'ficha' | 'competencia' | 'hallazgos' | 'plan' }[] = [
  { to: '', label: 'Resumen', end: true },
  { to: 'ficha', label: 'Ficha', checkpoint: 'ficha' },
  { to: 'datos', label: 'Datos del estudio' },
  { to: 'competencia', label: 'Competencia', checkpoint: 'competencia' },
  { to: 'diagnostico', label: 'Diagnóstico' },
  { to: 'hallazgos', label: 'Hallazgos', checkpoint: 'hallazgos' },
  { to: 'plan', label: 'Plan', checkpoint: 'plan' },
  { to: 'propuesta', label: 'Propuesta' },
  { to: 'calidad', label: 'Calidad y trazas' },
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

function ThemeToggle() {
  const { resolved, setChoice } = useTheme()
  const next = resolved === 'dark' ? 'light' : 'dark'
  return (
    <Button variant="ghost" size="sm" aria-label={resolved === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'} onClick={() => setChoice(next)}>
      {resolved === 'dark' ? <Sun size={16} strokeWidth={1.5} aria-hidden /> : <Moon size={16} strokeWidth={1.5} aria-hidden />}
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
  return (
    <nav className="sidenav" aria-label="Secciones del proyecto">
      <div className="side-project">
        <b>{project?.nombre ?? 'Proyecto'}</b>
        {estado && <Chip tone={estado.tone} dot>{estado.texto}</Chip>}
      </div>
      {SECTIONS.map((s) => {
        const approved = s.checkpoint && project ? project.checkpoints[s.checkpoint] : undefined
        return (
          <NavLink key={s.label} to={s.to === '' ? `/proyectos/${id}` : `/proyectos/${id}/${s.to}`} end={s.end} className="navlink" title={s.label}>
            <span className="navlabel">{s.label}</span>
            {s.checkpoint && project && (
              <span className="chip-dot" style={{ color: approved ? 'var(--good)' : 'var(--warn)' }} role="img" aria-label={approved ? 'Punto de control aprobado' : 'Punto de control pendiente'} />
            )}
          </NavLink>
        )
      })}
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
        <Link to="/" className="brandmark">GEO Copilot</Link>
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
