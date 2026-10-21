import { useMemo, useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import { Button, Chip, DataTable, Drawer, Input, Textarea } from '@/components'
import { formatEur } from '@/lib/format'
import type { PlanAccion, PlanAviso } from './api'
import { FASES, PALANCA, parseList, RESPONSABLE, TALLA, TALLAS } from './labels'

type Patch = Partial<PlanAccion>

const cell = 'w-full min-w-24 rounded border border-[var(--brand-neutral)]/40 bg-transparent px-1.5 py-1 text-sm'

function NumberCell({ value, label, onChange, min = 0 }: { value: number; label: string; onChange: (v: number) => void; min?: number }) {
  return <input className={`${cell} w-20 tabular-nums`} type="number" min={min} value={value} aria-label={label} onChange={(e) => onChange(Number(e.target.value))} />
}

function SelectCell<V extends string | number>({ value, label, options, onChange }: { value: V; label: string; options: { value: V; label: string }[]; onChange: (v: V) => void }) {
  return (
    <select className={cell} value={String(value)} aria-label={label} onChange={(e) => onChange((typeof value === 'number' ? Number(e.target.value) : e.target.value) as V)}>
      {options.map((o) => <option key={String(o.value)} value={String(o.value)}>{o.label}</option>)}
    </select>
  )
}

export function ActionsTable({ acciones, avisos, onEdit }: { acciones: PlanAccion[]; avisos: PlanAviso[]; onEdit: (id: string, patch: Patch) => void }) {
  const [openId, setOpenId] = useState<string | null>(null)
  const current = acciones.find((a) => a.id === openId) ?? null

  const columns = useMemo<ColumnDef<PlanAccion, unknown>[]>(() => {
    const avisosDe = (id: string) => avisos.filter((x) => x.accion_id === id)
    return [
      { header: 'Id', accessorKey: 'id', cell: ({ row }) => <span className="font-medium tabular-nums">{row.original.id}</span> },
      {
        header: 'Título',
        accessorKey: 'titulo',
        cell: ({ row }) => (
          <div className="flex min-w-56 items-start gap-2">
            <Input className={cell} value={row.original.titulo} aria-label={`Título de ${row.original.id}`} onChange={(e) => onEdit(row.original.id, { titulo: e.target.value })} />
            <Button className="shrink-0 rounded border border-[var(--brand-neutral)]/40 px-2 py-1 text-sm" aria-label={`Editar detalle de ${row.original.id}`} onClick={() => setOpenId(row.original.id)}>Detalle</Button>
          </div>
        ),
      },
      { header: 'Palanca', cell: ({ row }) => <SelectCell value={row.original.palanca} label={`Palanca de ${row.original.id}`} options={Object.entries(PALANCA).map(([value, label]) => ({ value: value as PlanAccion['palanca'], label }))} onChange={(palanca) => onEdit(row.original.id, { palanca })} /> },
      { header: 'Esfuerzo', cell: ({ row }) => <SelectCell value={row.original.esfuerzo} label={`Esfuerzo de ${row.original.id}`} options={TALLAS.map((t) => ({ value: t, label: TALLA[t] }))} onChange={(esfuerzo) => onEdit(row.original.id, { esfuerzo })} /> },
      { header: 'Impacto', cell: ({ row }) => <SelectCell value={row.original.impacto} label={`Impacto de ${row.original.id}`} options={TALLAS.map((t) => ({ value: t, label: TALLA[t] }))} onChange={(impacto) => onEdit(row.original.id, { impacto })} /> },
      { header: 'Responsable', cell: ({ row }) => <SelectCell value={row.original.responsable} label={`Responsable de ${row.original.id}`} options={Object.entries(RESPONSABLE).map(([value, label]) => ({ value: value as PlanAccion['responsable'], label }))} onChange={(responsable) => onEdit(row.original.id, { responsable })} /> },
      { header: 'Fase', cell: ({ row }) => <SelectCell value={row.original.fase_plan} label={`Fase de ${row.original.id}`} options={FASES.map((n) => ({ value: n, label: `Fase ${n}` }))} onChange={(fase_plan) => onEdit(row.original.id, { fase_plan })} /> },
      { header: 'Inicio (sem.)', cell: ({ row }) => <NumberCell value={row.original.semana_inicio} min={1} label={`Semana de inicio de ${row.original.id}`} onChange={(semana_inicio) => onEdit(row.original.id, { semana_inicio })} /> },
      { header: 'Duración (sem.)', cell: ({ row }) => <NumberCell value={row.original.plazo_semanas} min={1} label={`Duración en semanas de ${row.original.id}`} onChange={(plazo_semanas) => onEdit(row.original.id, { plazo_semanas })} /> },
      {
        header: 'Coste (€)',
        cell: ({ row }) => (
          <div className="flex flex-col items-end">
            <NumberCell value={row.original.coste_estimado_eur} label={`Coste de ${row.original.id}`} onChange={(coste_estimado_eur) => onEdit(row.original.id, { coste_estimado_eur })} />
            <span className="text-xs text-[var(--brand-neutral)]">{formatEur(row.original.coste_estimado_eur)}</span>
          </div>
        ),
      },
      {
        header: 'Avisos',
        cell: ({ row }) => {
          const list = avisosDe(row.original.id)
          if (list.length === 0) return <span className="text-[var(--brand-neutral)]">—</span>
          const tone = list.some((x) => x.nivel === 'error') ? 'bad' : 'warn'
          return <Chip tone={tone}>{`${list.length} ${list.length === 1 ? 'aviso' : 'avisos'}`}</Chip>
        },
      },
    ]
  }, [avisos, onEdit])

  return (
    <>
      <div className="overflow-x-auto">
        <DataTable columns={columns} data={acciones} editable />
      </div>
      <ActionDrawer accion={current} avisos={current ? avisos.filter((x) => x.accion_id === current.id) : []} onClose={() => setOpenId(null)} onEdit={onEdit} />
    </>
  )
}

/** Campo de lista con texto local: no pierde comas ni saltos de línea mientras se escribe. */
function ListField({ label, value, multiline, onChange }: { label: string; value: string[]; multiline?: boolean; onChange: (v: string[]) => void }) {
  const [text, setText] = useState(value.join(multiline ? '\n' : ', '))
  const change = (t: string) => {
    setText(t)
    onChange(parseList(t, multiline ? /\n/ : /,/))
  }
  return (
    <label className="grid gap-1 text-sm">
      {label}
      {multiline ? <Textarea className={cell} rows={4} value={text} onChange={(e) => change(e.target.value)} /> : <Input className={cell} value={text} onChange={(e) => change(e.target.value)} />}
    </label>
  )
}

function ActionDrawer({ accion, avisos, onClose, onEdit }: { accion: PlanAccion | null; avisos: PlanAviso[]; onClose: () => void; onEdit: (id: string, patch: Patch) => void }) {
  if (!accion) return <Drawer open={false} onOpenChange={onClose} title="Acción">{null}</Drawer>
  const set = (patch: Patch) => onEdit(accion.id, patch)
  return (
    <Drawer open onOpenChange={(o) => !o && onClose()} title={`${accion.id} · detalle de la acción`}>
      <div className="grid gap-3">
        {avisos.map((a) => <p key={a.texto} role="alert" className="text-sm">{a.texto}</p>)}
        <label className="grid gap-1 text-sm">Descripción<Textarea className={cell} rows={4} value={accion.descripcion} onChange={(e) => set({ descripcion: e.target.value })} /></label>
        <ListField key={`${accion.id}-h`} label="Hallazgos relacionados (separados por comas)" value={accion.hallazgos_relacionados} onChange={(v) => set({ hallazgos_relacionados: v })} />
        <ListField key={`${accion.id}-d`} label="Dependencias (ids de acción, separados por comas)" value={accion.dependencias ?? []} onChange={(v) => set({ dependencias: v })} />
        <ListField key={`${accion.id}-f`} label="Fases del embudo (separadas por comas)" value={accion.fase_embudo ?? []} onChange={(v) => set({ fase_embudo: v })} />
        <ListField key={`${accion.id}-m`} label="Motores (separados por comas)" value={accion.motores_objetivo ?? []} onChange={(v) => set({ motores_objetivo: v })} />
        <ListField key={`${accion.id}-c`} label="Ciudades (separadas por comas)" value={accion.ciudades ?? []} onChange={(v) => set({ ciudades: v })} />
        <ListField key={`${accion.id}-e`} label="Entregables (uno por línea)" multiline value={accion.entregables} onChange={(v) => set({ entregables: v })} />
        <label className="grid gap-1 text-sm">KPI de la acción<Input className={cell} value={accion.kpi} onChange={(e) => set({ kpi: e.target.value })} /></label>
      </div>
    </Drawer>
  )
}
