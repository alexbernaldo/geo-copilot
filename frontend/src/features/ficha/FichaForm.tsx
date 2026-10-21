import { useEffect, useId, type ReactNode } from 'react'
import { useController, useForm, type Control, type FieldPath } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button, Chip, Input, Textarea } from '@/components'
import { ETIQUETAS_SITUACION, fichaSchema, type FichaFormValues } from './fichaValores'

interface CampoProps {
  etiqueta: string
  ayuda?: string
  falta: boolean
  error?: string
  origen?: string
  children: (ids: { id: string; describedBy: string | undefined }) => ReactNode
}

function Campo({ etiqueta, ayuda, falta, error, origen, children }: CampoProps) {
  const id = useId()
  const descId = `${id}-d`
  const hay = Boolean(ayuda || error || origen)
  return (
    <div className="campo" data-falta={falta || undefined} data-invalid={error ? true : undefined}>
      <label htmlFor={id}>
        {etiqueta} {falta && <Chip tone="warn">Falta</Chip>}
      </label>
      {children({ id, describedBy: hay ? descId : undefined })}
      <div id={descId}>
        {ayuda && <small>{ayuda}</small>}
        {error && <p role="alert">{error}</p>}
        {origen && <blockquote>Extraído del brief: «{origen}»</blockquote>}
      </div>
    </div>
  )
}

const LISTA = 'Una por línea.'

/** Los componentes `Input`/`Textarea` del kit no reenvían `ref`, así que el campo va por `useController` (sin `register`). */
function Entrada({ control, name, id, multilinea, filas, describedBy, invalido }: {
  control: Control<FichaFormValues>
  name: FieldPath<FichaFormValues>
  id: string
  multilinea: boolean
  filas: number
  describedBy?: string
  invalido: boolean
}) {
  const { field } = useController({ control, name })
  const { ref: _ref, value, ...props } = field
  const comun = { id, 'aria-describedby': describedBy, 'aria-invalid': invalido ? true : undefined, value: typeof value === 'string' ? value : '' }
  return multilinea ? <Textarea rows={filas} {...comun} {...props} /> : <Input {...comun} {...props} />
}

/** Formulario completo de la ficha. Sin red: recibe valores y devuelve valores válidos en `onSubmit`. */
export function FichaForm({ valores, faltantes, origenCampos, guardando, onSubmit, onDirtyChange }: {
  valores: FichaFormValues
  faltantes: string[]
  origenCampos: Record<string, string>
  guardando?: boolean
  onSubmit: (v: FichaFormValues) => void
  onDirtyChange?: (dirty: boolean) => void
}) {
  const form = useForm<FichaFormValues>({ values: valores, resolver: zodResolver(fichaSchema), mode: 'onBlur' })
  const { control, handleSubmit, formState } = form
  const errores = formState.errors
  const sucio = formState.isDirty
  useEffect(() => { onDirtyChange?.(sucio) }, [sucio, onDirtyChange])

  const texto = (campo: FieldPath<FichaFormValues> & keyof FichaFormValues, etiqueta: string, opts: { ayuda?: string; lista?: boolean; filas?: number } = {}) => {
    const err = errores[campo]
    const mensaje = err && 'message' in err ? String(err.message) : undefined
    return (
      <Campo etiqueta={etiqueta} ayuda={opts.ayuda ?? (opts.lista ? LISTA : undefined)} falta={faltantes.includes(campo)} error={mensaje} origen={origenCampos[campo]}>
        {({ id, describedBy }) =>
          <Entrada control={control} name={campo} id={id} multilinea={Boolean(opts.lista || opts.filas)} filas={opts.filas ?? 4} describedBy={describedBy} invalido={Boolean(mensaje)} />
        }
      </Campo>
    )
  }

  const situacion = Object.keys(valores.situacion_digital)

  return (
    <form className="ficha-form" onSubmit={handleSubmit(onSubmit)} noValidate aria-label="Ficha de la marca">
      <fieldset>
        <legend>Identidad</legend>
        {texto('marca', 'Marca')}
        {texto('web', 'Web', { ayuda: 'Dirección completa, con https://.' })}
        {texto('sector', 'Sector')}
        {texto('subsector', 'Subsector')}
      </fieldset>
      <fieldset>
        <legend>Oferta</legend>
        {texto('servicios', 'Servicios', { lista: true })}
        {texto('servicios_prioritarios', 'Servicios prioritarios', { lista: true })}
        {texto('diferenciales', 'Diferenciales', { lista: true })}
      </fieldset>
      <fieldset>
        <legend>Mercado</legend>
        {texto('publicos', 'Públicos', { lista: true })}
        {texto('ciudades', 'Ciudades', { lista: true })}
        {texto('ciudad_principal', 'Ciudad principal')}
        {texto('ciudad_crecimiento', 'Ciudad de crecimiento')}
        {texto('competidores_declarados', 'Competidores declarados', { lista: true })}
      </fieldset>
      <fieldset>
        <legend>Situación y objetivos</legend>
        {situacion.map((clave) => (
          <Campo key={clave} etiqueta={ETIQUETAS_SITUACION[clave] ?? clave} falta={false}>
            {({ id }) => <Entrada control={control} name={`situacion_digital.${clave}`} id={id} multilinea filas={3} invalido={false} />}
          </Campo>
        ))}
        {texto('hipotesis_cliente', 'Hipótesis del cliente', { lista: true })}
        {texto('objetivo_principal', 'Objetivo principal', { filas: 3 })}
        {texto('kpis_negocio', 'KPIs de negocio', { lista: true })}
        {texto('horizonte_meses', 'Horizonte (meses)')}
      </fieldset>
      <fieldset>
        <legend>Recursos</legend>
        {texto('presupuesto_min_eur', 'Presupuesto mínimo (€)')}
        {texto('presupuesto_max_eur', 'Presupuesto máximo (€)')}
        {texto('equipo', 'Equipo', { filas: 3 })}
      </fieldset>
      <fieldset>
        <legend>Comunicación</legend>
        {texto('restricciones_normativas', 'Restricciones normativas', { lista: true })}
        {texto('tono', 'Tono')}
        {texto('audiencia', 'Audiencia')}
        {texto('formato', 'Formato')}
      </fieldset>
      <Button type="submit" variant="primary" disabled={!formState.isDirty || guardando}>{guardando ? 'Guardando…' : 'Guardar cambios'}</Button>
    </form>
  )
}
