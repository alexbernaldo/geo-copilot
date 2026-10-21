import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import type { Estimate } from '@/api/types'
import { formatEur, formatNum } from '@/lib/format'
import { Button, Tooltip } from './primitives'

export type Scope = 'espontanea' | 'asistida'
export type Origen = 'calculado' | 'ia' | 'automatico' | 'editado'
export type Tone = 'neutral' | 'good' | 'warn' | 'bad' | 'info' | 'spont' | 'assist' | 'accent'

export function Chip({ tone, dot, children }: { tone: Tone; dot?: boolean; children: ReactNode }) {
  return (
    <span className="chip" data-tone={tone}>
      {dot && <span className="chip-dot" aria-hidden />}
      <span>{children}</span>
    </span>
  )
}

/** Iniciales de una marca («Clínica Alborada Visión» -> «CA»), sin palabras vacías. */
export function initials(nombre: string): string {
  const vacias = new Set(['de', 'del', 'la', 'el', 'los', 'las', 'y', '·', 'ejemplo'])
  const palabras = nombre.split(/\s+/).filter((w) => w && !vacias.has(w.toLowerCase()))
  return palabras.slice(0, 2).map((w) => w[0]!.toUpperCase()).join('') || '·'
}

export function Avatar({ nombre, size }: { nombre: string; size?: 'lg' }) {
  return <span className="avatar" data-size={size} aria-hidden>{initials(nombre)}</span>
}

/** Marca de GEO Copilot: ondas de visibilidad que salen de un punto (la marca) con los colores de proyecto y espontánea. */
export function Logo({ size = 26 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <defs>
        <linearGradient id="geo-logo" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" style={{ stopColor: 'var(--brand-project)' }} />
          <stop offset="1" style={{ stopColor: 'var(--spont)' }} />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="url(#geo-logo)" />
      <circle cx="11" cy="21" r="3" fill="#fff" />
      <path d="M11 13.5a7.5 7.5 0 0 1 7.5 7.5" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" fill="none" opacity="0.9" />
      <path d="M11 7.5A13.5 13.5 0 0 1 24.5 21" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" fill="none" opacity="0.55" />
    </svg>
  )
}

export function PageHeader({ title, description, actions, checkpoint }: { title: string; description?: string; actions?: ReactNode; checkpoint?: { n: number; approved: boolean } }) {
  return (
    <header className="page-header">
      <div className="page-header-main">
        <h1 className="page-title">{title}</h1>
        {description && <p className="page-desc">{description}</p>}
        {checkpoint && (
          <div className="page-meta">
            <Chip tone={checkpoint.approved ? 'good' : 'warn'} dot>{`Punto de control ${checkpoint.n}: ${checkpoint.approved ? 'aprobado' : 'pendiente'}`}</Chip>
          </div>
        )}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  )
}

export function Panel({ title, source, actions, children }: { title?: string; source?: ReactNode; actions?: ReactNode; children: ReactNode }) {
  const head = title || source || actions
  return (
    <section className="panel" aria-label={title}>
      {head && (
        <div className="panel-head">
          {title ? <h2 className="panel-title">{title}</h2> : <span />}
          <div className="panel-tools">{source}{actions}</div>
        </div>
      )}
      <div className="panel-body">{children}</div>
    </section>
  )
}

export interface KpiItem { label: string; value: string | number; unit?: string; note?: string; source?: ReactNode; highlight?: boolean }

export function KpiStrip({ items, scope }: { items: KpiItem[]; scope?: Scope }) {
  return (
    <dl className="kpis" data-scope={scope}>
      {items.map((i) => (
        <div className="kpi" key={i.label} data-highlight={i.highlight || undefined}>
          <dt>{i.label}</dt>
          <dd className="kpi-value">{i.value}{i.unit && <span className="kpi-unit">{i.unit}</span>}</dd>
          {i.note && <dd className="kpi-note">{i.note}</dd>}
          {i.source && <dd className="kpi-source">{i.source}</dd>}
        </div>
      ))}
    </dl>
  )
}

export function ScopeToggle({ value, onChange }: { value: Scope; onChange: (v: Scope) => void }) {
  return (
    <div className="scope" role="group" aria-label="Ámbito">
      {(['espontanea', 'asistida'] as const).map((s) => (
        <button key={s} type="button" data-scope={s} aria-pressed={value === s} onClick={() => onChange(s)}>{s === 'espontanea' ? 'Espontánea' : 'Asistida'}</button>
      ))}
    </div>
  )
}

const ORIGEN_TEXTO: Record<Origen, string> = { calculado: 'Calculado', ia: 'Redactado por IA', automatico: 'Generado automáticamente', editado: 'Editado' }

export function OriginTag({ origen, modelo }: { origen: Origen; modelo?: string | null }) {
  return <Chip tone={origen === 'ia' ? 'info' : 'neutral'}>{origen === 'ia' && modelo ? `${ORIGEN_TEXTO.ia} · ${modelo}` : ORIGEN_TEXTO[origen]}</Chip>
}

export function SourceNote({ tabla, n }: { tabla: string; n: number }) {
  return (
    <Tooltip content={`Origen: ${tabla} · n=${formatNum(n)}`}>
      <span className="source-note" tabIndex={0}>{`${tabla} · n=${formatNum(n)}`}</span>
    </Tooltip>
  )
}

export function EvidenceLink({ ids, label = 'Ver evidencia' }: { ids: string[]; label?: string }) {
  const { pathname } = useLocation()
  const base = pathname.match(/^\/proyectos\/[^/]+/)?.[0] ?? '/proyectos'
  return <Link className="link" to={`${base}/datos?ids=${encodeURIComponent(ids.join(','))}`}>{label}</Link>
}

function StateBox({ kind, title, description, children, role }: { kind: string; title: string; description: string; children?: ReactNode; role?: 'status' | 'alert' }) {
  return (
    <div className="state" data-kind={kind} role={role}>
      <h2 className="state-title">{title}</h2>
      <p className="state-desc">{description}</p>
      {children && <div>{children}</div>}
    </div>
  )
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <StateBox kind="empty" title={title} description={description} role="status">{action}</StateBox>
}

export function PendingState({ step }: { step: string }) {
  return <StateBox kind="pending" title="Todavía no disponible" description={`Disponible cuando termine el paso ${step}.`} role="status" />
}

export function errorMessage(error: unknown): string {
  if (typeof error === 'object' && error && 'error' in error) {
    const m = (error as { error?: { message?: string } }).error?.message
    if (m) return m
  }
  if (error instanceof Error && error.message) return error.message
  return 'Ha ocurrido un error.'
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <StateBox kind="error" title="No se ha podido completar la acción" description={errorMessage(error)} role="alert">
      {onRetry && <Button onClick={onRetry}>Reintentar</Button>}
    </StateBox>
  )
}

export function Skeleton({ height = 16, width = '100%' }: { height?: number; width?: number | string }) {
  return <div className="skeleton" style={{ height, width }} aria-hidden />
}

export function CheckpointBar({ n, approved, onApprove, summary }: { n: number; approved: boolean; onApprove: () => void; summary: ReactNode }) {
  return (
    <div className="checkpoint" role="region" aria-label={`Punto de control ${n}`} data-approved={approved}>
      <div className="checkpoint-summary">
        <div className="checkpoint-n">{`Punto de control ${n}`}</div>
        <div>{summary}</div>
      </div>
      {approved ? <Chip tone="good" dot>Aprobado</Chip> : <Button variant="primary" onClick={onApprove}>Aprobar</Button>}
    </div>
  )
}

export function CostConfirm({ estimate, onConfirm, onCancel }: { estimate: Estimate; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="cost" role="group" aria-label="Confirmar coste">
      <dl className="cost-total">
        <div><dt>Llamadas</dt><dd>{formatNum(estimate.total_llamadas)}</dd></div>
        <div><dt>Coste previsto</dt><dd>{formatEur(estimate.total_eur, 2)}</dd></div>
        <div><dt>Tiempo</dt><dd>{`${formatNum(estimate.minutos, 1)} min`}</dd></div>
      </dl>
      {estimate.pasos.length > 0 && (
        <table className="table">
          <thead><tr><th scope="col">Paso</th><th scope="col" data-num="true">Llamadas</th><th scope="col" data-num="true">Coste</th></tr></thead>
          <tbody>{estimate.pasos.map((p) => <tr key={p.id}><td>{p.nombre}</td><td data-num="true">{formatNum(p.llamadas)}</td><td data-num="true">{formatEur(p.eur, 2)}</td></tr>)}</tbody>
        </table>
      )}
      {estimate.supera_tope && <p className="alert" role="alert">{`Supera el tope de gasto por proyecto (${formatEur(estimate.tope_eur, 2)}). Reduce el estudio o sube el tope en Ajustes.`}</p>}
      <div className="cost-actions">
        <Button onClick={onCancel}>Cancelar</Button>
        <Button variant="primary" disabled={estimate.supera_tope} onClick={onConfirm}>Confirmar coste</Button>
      </div>
    </div>
  )
}
