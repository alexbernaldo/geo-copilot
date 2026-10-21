import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Chip, Dialog, EmptyState, Input, PageHeader, Panel } from '@/components'
import type { Tone } from '@/components'
import { api } from '@/api/client'
import { formatDate, formatEur } from '@/lib/format'
import type { components } from '@/api/schema'

type Project = components['schemas']['Project']

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
    <div className="grid gap-6">
      <PageHeader
        title="Proyectos"
        description="Auditorías de optimización para motores generativos (GEO) y análisis comparativos."
        actions={
          <Button variant="primary" onClick={() => navigate('/proyectos/nuevo')}>
            Nuevo proyecto
          </Button>
        }
      />

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input
            placeholder="Buscar por nombre o marca..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-64"
          />
          <div className="flex items-center gap-1.5 text-xs">
            <span className="text-[var(--fg-muted)]">Estado:</span>
            {['todos', 'borrador', 'en_ejecucion', 'esperando_revision', 'completado'].map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => setFiltroEstado(st)}
                className="cursor-pointer"
              >
                <Chip tone={filtroEstado === st ? 'accent' : 'neutral'}>
                  {st === 'todos' ? 'Todos' : st.replace('_', ' ')}
                </Chip>
              </button>
            ))}
          </div>
        </div>

        <label className="flex items-center gap-2 text-xs text-[var(--fg-muted)] cursor-pointer">
          <input
            type="checkbox"
            checked={verArchivados}
            onChange={(e) => setVerArchivados(e.target.checked)}
          />
          Ver archivados
        </label>
      </div>

      {isLoading ? (
        <Panel>
          <div className="py-12 text-center text-sm text-[var(--fg-muted)]">
            Cargando proyectos...
          </div>
        </Panel>
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
        <div className="grid gap-3">
          {filtrados.map((p) => (
            <Panel key={p.id}>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="grid gap-1">
                  <div className="flex items-center gap-2.5">
                    <Link
                      to={`/proyectos/${p.id}`}
                      className="font-semibold hover:text-[var(--brand-project)]"
                    >
                      {p.nombre}
                    </Link>
                    <ProjectStatusChip status={p.estado} />
                    {p.archivado && <Chip tone="neutral">Archivado</Chip>}
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--fg-muted)]">
                    {p.marca && <span>Marca: <strong className="text-[var(--fg)]">{p.marca}</strong></span>}
                    {p.sector && <span>Sector: {p.sector}</span>}
                    <span>Tipo: {p.tipo}</span>
                    <span>Coste: {formatEur(p.coste_eur)}</span>
                    <span>Actualizado: {formatDate(p.actualizado)}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => navigate(`/proyectos/${p.id}`)}
                  >
                    Abrir
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => mutDuplicate.mutate(p.id)}
                  >
                    Duplicar
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setRenombrando(p)
                      setNuevoNombre(p.nombre)
                    }}
                  >
                    Renombrar
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => mutArchive.mutate({ id: p.id, archivado: !p.archivado })}
                  >
                    {p.archivado ? 'Desarchivar' : 'Archivar'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-[var(--bad)] hover:bg-[var(--bad)]/10"
                    onClick={() => {
                      setBorrando(p)
                      setConfirmBorrado('')
                    }}
                  >
                    Borrar
                  </Button>
                </div>
              </div>
            </Panel>
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
