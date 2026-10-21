import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Building2, Clock, Search } from 'lucide-react'
import { Avatar, Button, Checkbox, Chip, Dialog, EmptyState, Input, PageHeader, Panel, Skeleton } from '@/components'
import type { Tone } from '@/components'
import { api } from '@/api/client'
import { formatDate, formatEur } from '@/lib/format'
import type { components } from '@/api/schema'

type Project = components['schemas']['Project']

const FILTROS = [
  { valor: 'todos', texto: 'Todos' },
  { valor: 'borrador', texto: 'Borrador' },
  { valor: 'en_ejecucion', texto: 'En ejecución' },
  { valor: 'esperando_revision', texto: 'Esperando revisión' },
  { valor: 'completado', texto: 'Completados' },
]

function ProjectStatusChip({ status }: { status: string }) {
  const map: Record<string, { tone: Tone; label: string }> = {
    borrador: { tone: 'neutral', label: 'Borrador' },
    listo_para_lanzar: { tone: 'info', label: 'Listo' },
    en_ejecucion: { tone: 'accent', label: 'En ejecución' },
    esperando_revision: { tone: 'warn', label: 'Revisión pendiente' },
    completado: { tone: 'good', label: 'Completado' },
    error: { tone: 'bad', label: 'Error' },
    interrumpido: { tone: 'warn', label: 'Interrumpido' },
  }
  const entry = map[status] ?? { tone: 'neutral', label: status }
  return <Chip tone={entry.tone} dot>{entry.label}</Chip>
}

export default function ProyectosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [q, setQ] = useState('')
  const [filtroEstado, setFiltroEstado] = useState<string>('todos')
  const [verArchivados, setVerArchivados] = useState(false)

  // Modales
  const [renombrando, setRenombrando] = useState<Project | null>(null)
  const [nuevoNombre, setNuevoNombre] = useState('')
  const [borrando, setBorrando] = useState<Project | null>(null)
  const [confirmBorrado, setConfirmBorrado] = useState('')

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects', filtroEstado, verArchivados],
    queryFn: async () => {
      const res = await api.GET('/projects', {
        params: {
          query: {
            estado: filtroEstado !== 'todos' ? filtroEstado : undefined,
            archivados: verArchivados,
          },
        },
      })
      return (res.data as Project[]) ?? []
    },
  })

  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const res = await api.GET('/settings', {})
      return res.data
    },
  })

  // Mutaciones
  const mutRename = useMutation({
    mutationFn: async ({ id, nombre }: { id: string; nombre: string }) => {
      await api.PATCH('/projects/{id}', {
        params: { path: { id } },
        body: { nombre },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setRenombrando(null)
    },
  })

  const mutArchive = useMutation({
    mutationFn: async ({ id, archivado }: { id: string; archivado: boolean }) => {
      await api.PATCH('/projects/{id}', {
        params: { path: { id } },
        body: { archivado },
      })
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
  })

  const mutDuplicate = useMutation({
    mutationFn: async (id: string) => {
      const res = await api.POST('/projects/{id}/duplicate', {
        params: { path: { id } },
      })
      return res.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      if (data && 'id' in data) navigate(`/proyectos/${data.id}`)
    },
  })

  const mutDelete = useMutation({
    mutationFn: async ({ id, confirm }: { id: string; confirm: string }) => {
      await api.DELETE('/projects/{id}', {
        params: { path: { id }, query: { confirm } },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setBorrando(null)
      setConfirmBorrado('')
    },
  })

  const filtrados = useMemo(() => {
    let list = projects
    if (q.trim()) {
      const needle = q.toLowerCase().trim()
      list = list.filter(
        (p) =>
          p.nombre.toLowerCase().includes(needle) ||
          (p.marca && p.marca.toLowerCase().includes(needle)),
      )
    }
    return list
  }, [projects, q])

  return (
    <div className="grid gap-5">
      <PageHeader
        title="Proyectos"
        description="Auditorías de optimización para motores generativos (GEO) y análisis comparativos."
        actions={
          <Button variant="primary" onClick={() => navigate('/proyectos/nuevo')}>
            Nuevo proyecto
          </Button>
        }
      />

      <div className="toolbar">
        <div className="toolbar-left">
          <div className="search">
            <Search size={15} strokeWidth={1.75} aria-hidden />
            <Input placeholder="Buscar por nombre o marca" aria-label="Buscar proyectos" value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <div className="segmented" role="group" aria-label="Filtrar por estado">
            {FILTROS.map((f) => (
              <button key={f.valor} type="button" aria-pressed={filtroEstado === f.valor} onClick={() => setFiltroEstado(f.valor)}>
                {f.texto}
              </button>
            ))}
          </div>
        </div>
        <Checkbox checked={verArchivados} onCheckedChange={setVerArchivados} label="Ver archivados" />
      </div>

      {isLoading ? (
        <div className="project-list" aria-busy>
          {[0, 1].map((i) => <Skeleton key={i} height={84} />)}
        </div>
      ) : filtrados.length === 0 ? (
        <Panel>
          <EmptyState
            title="Sin proyectos que mostrar"
            description="GEO Copilot evalúa la visibilidad de marcas en asistentes de IA y redacta planes de optimización fundamentados en datos reales."
            action={
              <div className="flex items-center justify-center gap-3 mt-4">
                <Button variant="primary" onClick={() => navigate('/proyectos/nuevo')}>
                  Nuevo proyecto
                </Button>
                {!settings?.clave_configurada && (
                  <Button variant="default" onClick={() => navigate('/ajustes')}>
                    Configurar OpenRouter
                  </Button>
                )}
              </div>
            }
          />
        </Panel>
      ) : (
        <div className="project-list">
          {filtrados.map((p) => (
            <article key={p.id} className="project-card">
              <Avatar nombre={p.marca ?? p.nombre} size="lg" />
              <div className="project-card-main">
                <div className="project-card-title">
                  <Link to={`/proyectos/${p.id}`} className="project-name">{p.nombre}</Link>
                  <ProjectStatusChip status={p.estado} />
                  {p.archivado && <Chip tone="neutral">Archivado</Chip>}
                </div>
                <div className="project-meta">
                  {p.marca && <span><Building2 size={13} strokeWidth={1.75} aria-hidden /><b>{p.marca}</b></span>}
                  {p.sector && <span>{p.sector}</span>}
                  <span>{p.tipo === 'cliente' ? 'Cliente' : 'Prospecto'}</span>
                  <span className="num">{formatEur(p.coste_eur, 2)}</span>
                  <span><Clock size={13} strokeWidth={1.75} aria-hidden />{formatDate(p.actualizado)}</span>
                </div>
              </div>
              <div className="project-actions">
                <Button variant="ghost" size="sm" onClick={() => mutDuplicate.mutate(p.id)}>Duplicar</Button>
                <Button variant="ghost" size="sm" onClick={() => { setRenombrando(p); setNuevoNombre(p.nombre) }}>Renombrar</Button>
                <Button variant="ghost" size="sm" onClick={() => mutArchive.mutate({ id: p.id, archivado: !p.archivado })}>{p.archivado ? 'Desarchivar' : 'Archivar'}</Button>
                <Button variant="ghost" size="sm" data-tone="bad" onClick={() => { setBorrando(p); setConfirmBorrado('') }}>Borrar</Button>
                <Button size="sm" onClick={() => navigate(`/proyectos/${p.id}`)}>Abrir <ArrowRight size={14} strokeWidth={1.75} aria-hidden /></Button>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Dialog Renombrar */}
      <Dialog
        open={Boolean(renombrando)}
        onOpenChange={(open) => !open && setRenombrando(null)}
        title="Renombrar proyecto"
      >
        <div className="grid gap-3 py-2">
          <label className="text-xs text-[var(--fg-muted)]">Nuevo nombre</label>
          <Input
            value={nuevoNombre}
            onChange={(e) => setNuevoNombre(e.target.value)}
            autoFocus
          />
          <div className="flex justify-end gap-2 mt-2">
            <Button variant="ghost" onClick={() => setRenombrando(null)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              disabled={!nuevoNombre.trim()}
              onClick={() => {
                if (renombrando) {
                  mutRename.mutate({ id: renombrando.id, nombre: nuevoNombre.trim() })
                }
              }}
            >
              Guardar
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Dialog Borrar */}
      <Dialog
        open={Boolean(borrando)}
        onOpenChange={(open) => !open && setBorrando(null)}
        title="Borrar proyecto"
      >
        <div className="grid gap-3 py-2 text-sm">
          <p>
            Esta acción no se puede deshacer. Para confirmar, escribe el nombre exacto del proyecto:
          </p>
          <p className="font-mono text-xs bg-[var(--surface-2)] p-2 rounded">
            {borrando?.nombre}
          </p>
          <Input
            placeholder="Escribe el nombre aquí..."
            value={confirmBorrado}
            onChange={(e) => setConfirmBorrado(e.target.value)}
            autoFocus
          />
          <div className="flex justify-end gap-2 mt-2">
            <Button variant="ghost" onClick={() => setBorrando(null)}>
              Cancelar
            </Button>
            <Button
              variant="danger"
              disabled={confirmBorrado !== (borrando?.nombre ?? '')}
              onClick={() => {
                if (borrando) {
                  mutDelete.mutate({ id: borrando.id, confirm: confirmBorrado })
                }
              }}
            >
              Eliminar definitivamente
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  )
}
