import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { Estimate } from '@/api/types'
import { formatEur, formatNum } from '@/lib/format'

export type Scope = 'espontanea' | 'asistida'
export type Origen = 'calculado' | 'ia' | 'automatico' | 'editado'

export function PageHeader({ title, description, actions, checkpoint }: { title: string; description?: string; actions?: ReactNode; checkpoint?: { n: number; approved: boolean } }) {
  return (
    <header>
      <h1>{title}</h1>
      {description && <p>{description}</p>}
      {checkpoint && <Chip tone={checkpoint.approved ? 'good' : 'warn'}>{`Punto de control ${checkpoint.n}: ${checkpoint.approved ? 'aprobado' : 'pendiente'}`}</Chip>}
      {actions}
    </header>
  )
}

export function Panel({ title, source, actions, children }: { title?: string; source?: ReactNode; actions?: ReactNode; children: ReactNode }) {
  return (
    <section>
      {title && <h2>{title}</h2>}
      {source}
      {actions}
      {children}
    </section>
  )
}

export interface KpiItem { label: string; value: string | number; unit?: string; note?: string; source?: ReactNode; highlight?: boolean }

export function KpiStrip({ items, scope }: { items: KpiItem[]; scope?: Scope }) {
  return (
    <dl data-scope={scope}>
      {items.map((i) => (
        <div key={i.label} data-highlight={i.highlight || undefined}>
          <dt>{i.label}</dt>
          <dd>{i.value}{i.unit ? ` ${i.unit}` : ''}</dd>
          {i.note && <dd>{i.note}</dd>}
          {i.source}
        </div>
      ))}
    </dl>
  )
}

export function ScopeToggle({ value, onChange }: { value: Scope; onChange: (v: Scope) => void }) {
  return (
    <div role="group" aria-label="Ámbito">
      {(['espontanea', 'asistida'] as const).map((s) => (
        <button key={s} type="button" aria-pressed={value === s} onClick={() => onChange(s)}>{s === 'espontanea' ? 'Espontánea' : 'Asistida'}</button>
      ))}
    </div>
  )
}

export type Tone = 'neutral' | 'good' | 'warn' | 'bad' | 'info' | 'spont' | 'assist' | 'accent'

export function Chip({ tone, dot, children }: { tone: Tone; dot?: boolean; children: ReactNode }) {
  return <span data-tone={tone}>{dot && '● '}{children}</span>
}

const ORIGEN_TEXTO: Record<Origen, string> = { calculado: 'Calculado', ia: 'Redactado por IA', automatico: 'Generado automáticamente', editado: 'Editado' }

export function OriginTag({ origen, modelo }: { origen: Origen; modelo?: string | null }) {
  return <Chip tone={origen === 'ia' ? 'info' : 'neutral'}>{origen === 'ia' && modelo ? `${ORIGEN_TEXTO.ia} · ${modelo}` : ORIGEN_TEXTO[origen]}</Chip>
}

export function SourceNote({ tabla, n }: { tabla: string; n: number }) {
  return <small title={`Origen: ${tabla} · n=${n}`}>{`${tabla} · n=${formatNum(n)}`}</small>
}

export function EvidenceLink({ ids, label = 'Ver evidencia' }: { ids: string[]; label?: string }) {
  const { pathname } = window.location
  const base = pathname.match(/^\/proyectos\/[^/]+/)?.[0] ?? '/proyectos'
  return <Link to={`${base}/datos?ids=${encodeURIComponent(ids.join(','))}`}>{label}</Link>
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div role="status">
      <h2>{title}</h2>
      <p>{description}</p>
      {action}
    </div>
  )
}

export function PendingState({ step }: { step: string }) {
  return <EmptyState title="Todavía no disponible" description={`Disponible cuando termine el paso ${step}.`} />
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const msg = typeof error === 'object' && error && 'error' in error ? String((error as { error: { message?: string } }).error.message ?? '') : error instanceof Error ? error.message : 'Ha ocurrido un error.'
  return (
    <div role="alert">
      <p>{msg || 'Ha ocurrido un error.'}</p>
      {onRetry && <button type="button" onClick={onRetry}>Reintentar</button>}
    </div>
  )
}

export function CheckpointBar({ n, approved, onApprove, summary }: { n: number; approved: boolean; onApprove: () => void; summary: ReactNode }) {
  return (
    <div role="region" aria-label={`Punto de control ${n}`}>
      <div>{summary}</div>
      {approved ? <Chip tone="good">Aprobado</Chip> : <button type="button" onClick={onApprove}>Aprobar</button>}
    </div>
  )
}

export function CostConfirm({ estimate, onConfirm, onCancel }: { estimate: Estimate; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div role="dialog" aria-label="Confirmar coste">
      <p>{`${formatNum(estimate.total_llamadas)} llamadas · ${formatEur(estimate.total_eur, 2)} · ${formatNum(estimate.minutos)} min`}</p>
      {estimate.supera_tope && <p role="alert">{`Supera el tope de gasto (${formatEur(estimate.tope_eur, 2)}).`}</p>}
      <button type="button" onClick={onCancel}>Cancelar</button>
      <button type="button" disabled={estimate.supera_tope} onClick={onConfirm}>Confirmar</button>
    </div>
  )
}
