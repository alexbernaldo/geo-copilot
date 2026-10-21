import { useState } from 'react'
import type { Hallazgo } from '@/api/types'
import { Button, Chip, Dialog, EvidenceLink, Input, OriginTag, SourceNote, Textarea } from '@/components'
import { formatValor } from '@/features/data/common'
import type { FindingPatch } from './api'
import { estadoHallazgo } from './estado'

const TONO_IMPACTO = { alto: 'bad', medio: 'warn', bajo: 'neutral' } as const
const TONO_CONFIANZA = { alta: 'good', media: 'info', baja: 'warn' } as const

/** Tarjeta de un hallazgo. La descripción con cifras la genera el código y no se edita a mano. */
export function HallazgoCard({ hallazgo: h, ocupado, onPatch }: {
  hallazgo: Hallazgo
  ocupado: boolean
  onPatch: (cambio: FindingPatch) => void
}) {
  const estado = estadoHallazgo(h)
  const [editando, setEditando] = useState(false)
  const [titulo, setTitulo] = useState(h.titulo)
  const [descartando, setDescartando] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [nota, setNota] = useState(h.nota ?? '')
  const [verEvidencias, setVerEvidencias] = useState(false)

  const guardarTitulo = () => {
    const limpio = titulo.trim()
    if (limpio && limpio !== h.titulo) onPatch({ titulo: limpio })
    setEditando(false)
  }

  return (
    <article className="finding" aria-labelledby={`h-${h.id}`} data-estado={estado}>
      <header>
        <p className="finding-top">
          <strong className="finding-id">{h.id}</strong> <Chip tone="neutral">Prioridad {h.prioridad}</Chip>{' '}
          {estado === 'aprobado' && <Chip tone="good">Aprobado</Chip>}
          {estado === 'descartado' && <Chip tone="bad">Descartado</Chip>}
          {estado === 'pendiente' && <Chip tone="warn">Pendiente de revisar</Chip>}
        </p>
        {editando ? (
          <div className="finding-edit">
            <Input aria-label={`Título de ${h.id}`} value={titulo} onChange={(e) => setTitulo(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') guardarTitulo(); if (e.key === 'Escape') { setTitulo(h.titulo); setEditando(false) } }} />
            <Button onClick={guardarTitulo} disabled={ocupado}>Guardar título</Button>
            <Button onClick={() => { setTitulo(h.titulo); setEditando(false) }}>Cancelar</Button>
          </div>
        ) : (
          <h3 id={`h-${h.id}`}>{h.titulo}</h3>
        )}
      </header>
      <p className="finding-desc">{h.descripcion}</p>
      <p className="finding-tags">
        <Chip tone="info">{h.tipo}</Chip> {h.fase_embudo && <Chip tone="neutral">{h.fase_embudo}</Chip>}{' '}
        <Chip tone={TONO_IMPACTO[h.impacto]}>Impacto {h.impacto}</Chip> <Chip tone={TONO_CONFIANZA[h.confianza]}>Confianza {h.confianza}</Chip>
        {(h.motores ?? []).length > 0 && <Chip tone="neutral">{`Motores: ${(h.motores ?? []).join(', ')}`}</Chip>}
        <OriginTag origen={h.origen?.origen ?? 'calculado'} modelo={h.origen?.modelo} />
      </p>
      {h.descartado_motivo && <p>Motivo del descarte: {h.descartado_motivo}</p>}
      {h.nota && <p>Nota: {h.nota}</p>}

      <footer className="finding-actions">
      <Button variant="ghost" size="sm" onClick={() => setVerEvidencias((v) => !v)} aria-expanded={verEvidencias}>
        {verEvidencias ? 'Ocultar evidencias' : 'Ver evidencias'}
      </Button>
      <span className="finding-spacer" />
        <Button size="sm" onClick={() => onPatch({ aprobado: true })} disabled={ocupado || estado === 'aprobado'}>Aprobar</Button>
        <Button size="sm" variant="ghost" onClick={() => setDescartando(true)} disabled={ocupado || estado === 'descartado'}>Descartar</Button>
        <Button size="sm" variant="ghost" onClick={() => setEditando(true)} disabled={ocupado || editando}>Editar título</Button>
      </footer>
      {verEvidencias && (
        <ul className="finding-evidence" aria-label={`Evidencias de ${h.id}`}>
          {h.evidencias.map((e, i) => (
            <li key={`${e.metrica}-${i}`}>
              <code>{e.metrica}</code> = {formatValor(e.valor)} <SourceNote tabla={e.tabla} n={e.n} />{' '}
              {e.ejecucion_ids.length > 0 && <EvidenceLink ids={e.ejecucion_ids} label="Ver ejecuciones" />}
            </li>
          ))}
        </ul>
      )}


      <Dialog open={descartando} onOpenChange={setDescartando} title={`Descartar ${h.id}`}>
        <p>La descripción con cifras la genera el código y no se puede editar. Si no estás de acuerdo, descarta el hallazgo y deja una nota.</p>
        <label htmlFor={`m-${h.id}`}>Motivo del descarte</label>
        <Textarea id={`m-${h.id}`} rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
        <label htmlFor={`n-${h.id}`}>Nota (opcional)</label>
        <Textarea id={`n-${h.id}`} rows={3} value={nota} onChange={(e) => setNota(e.target.value)} />
        <Button
          disabled={motivo.trim() === '' || ocupado}
          onClick={() => {
            onPatch({ aprobado: false, descartado_motivo: motivo.trim(), ...(nota.trim() ? { nota: nota.trim() } : {}) })
            setDescartando(false)
            setMotivo('')
          }}
        >
          Descartar hallazgo
        </Button>
      </Dialog>
    </article>
  )
}
