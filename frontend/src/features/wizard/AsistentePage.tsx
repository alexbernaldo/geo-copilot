import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Button, Input, PageHeader, Panel, Textarea } from '@/components'
import { api } from '@/api/client'
import { formatEur } from '@/lib/format'
import type { components } from '@/api/schema'

type FichaPreview = components['schemas']['FichaPreview']
type StudySummary = components['schemas']['StudySummary']
type Estimate = components['schemas']['Estimate']

interface UploadReportItem {
  archivo: string
  tipo?: string
  filas: number
  avisos?: string[]
  errores?: string[]
}

interface BrandItem {
  nombre: string
  nivel: 'foco' | 'competidor_primario' | 'competidor_secundario'
  web?: string | null
}

export default function AsistentePage() {
  const navigate = useNavigate()
  const [paso, setPaso] = useState<1 | 2 | 3 | 4>(1)

  // Paso 1
  const [tipo, setTipo] = useState<'cliente' | 'prospecto'>('cliente')
  const [nombre, setNombre] = useState('')
  const [projectId, setProjectId] = useState<string | null>(null)

  // Paso 2: Cliente
  const [briefTexto, setBriefTexto] = useState('')
  const [fichaPreview, setFichaPreview] = useState<FichaPreview | null>(null)

  // Paso 2: Prospecto
  const [prospectMarca, setProspectMarca] = useState('')
  const [prospectDominio, setProspectDominio] = useState('')
  const [prospectSector, setProspectSector] = useState('')
  const [prospectCiudad, setProspectCiudad] = useState('')
  const [prospectCompetidores, setProspectCompetidores] = useState('')

  // Paso 3: Pestaña (subir CSV o en vivo)
  const [pestanaDatos, setPestanaDatos] = useState<'csv' | 'vivo'>('csv')
  const [uploadReports, setUploadReports] = useState<UploadReportItem[]>([])
  const [studySummary, setStudySummary] = useState<StudySummary | null>(null)

  // Paso 3: En vivo
  const [marcasEstudio, setMarcasEstudio] = useState<BrandItem[]>([])
  const [promptsEstudio, setPromptsEstudio] = useState<any[]>([])
  const [tamanoEstudio, setTamanoEstudio] = useState<'rapido' | 'estandar' | 'completo'>('estandar')

  // Paso 4: Ejecución
  const [revision, setRevision] = useState<'pausas' | 'continuo'>('pausas')
  const [confirmoCoste, setConfirmoCoste] = useState(false)

  // Settings para clave y modelos
  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const res = await api.GET('/settings', {})
      return res.data
    },
  })

  // Estimación total
  const { data: estimacionTotal } = useQuery({
    queryKey: ['estimates', projectId, pestanaDatos],
    queryFn: async () => {
      if (!projectId) return null
      const res = await api.GET('/estimates/analysis', {
        params: { query: { project_id: projectId } },
      })
      return (res.data as Estimate) ?? null
    },
    enabled: Boolean(projectId && paso >= 3),
  })

  // Mutación crear proyecto (Paso 1)
  const mutCrear = useMutation({
    mutationFn: async () => {
      const res = await api.POST('/projects', {
        body: {
          nombre: nombre.trim() || (tipo === 'cliente' ? 'Nuevo análisis' : prospectMarca.trim() || 'Nuevo prospecto'),
          tipo,
        },
      })
      return res.data
    },
    onSuccess: (data) => {
      if (data && 'id' in data) {
        setProjectId(data.id)
        setPaso(2)
      }
    },
  })

  // Mutación brief (Paso 2 cliente)
  const mutBrief = useMutation({
    mutationFn: async (texto: string) => {
      if (!projectId) return null
      const res = await api.POST('/projects/{id}/brief', {
        params: { path: { id: projectId } },
        body: { texto },
      })
      return (res.data as FichaPreview) ?? null
    },
    onSuccess: (data) => {
      if (data) {
        setFichaPreview(data)
        if (data.ficha?.marca && !nombre) {
          setNombre(`Auditoría GEO · ${data.ficha.marca}`)
        }
      }
    },
  })

  // Mutación prospecto (Paso 2 prospecto)
  const mutProspect = useMutation({
    mutationFn: async () => {
      if (!projectId) return null
      const comps = prospectCompetidores
        .split('\n')
        .map((c) => c.trim())
        .filter(Boolean)
      const res = await api.POST('/projects/{id}/prospect', {
        params: { path: { id: projectId } },
        body: {
          marca: prospectMarca.trim(),
          dominio: prospectDominio.trim(),
          sector: prospectSector.trim(),
          ciudad: prospectCiudad.trim(),
          competidores: comps,
        },
      })
      return (res.data as FichaPreview) ?? null
    },
    onSuccess: (data) => {
      if (data) setFichaPreview(data)
    },
  })

  // Mutación subir CSVs (Paso 3)
  const mutUpload = useMutation({
    mutationFn: async (fileList: FileList) => {
      if (!projectId) return null
      const formData = new FormData()
      for (let i = 0; i < fileList.length; i++) {
        const file = fileList[i]
        if (file) formData.append('archivos', file)
      }
      const response = await fetch(`/api/projects/${projectId}/study/upload`, {
        method: 'POST',
        body: formData,
      })
      return await response.json()
    },
    onSuccess: (data) => {
      if (data) {
        setUploadReports(data.informes || [])
        if (data.resumen) setStudySummary(data.resumen)
      }
    },
  })

  // Mutación proponer marcas (Paso 3 vivo)
  const mutProposeBrands = useMutation({
    mutationFn: async () => {
      if (!projectId) return null
      const res = await api.POST('/projects/{id}/study/brands/propose', {
        params: { path: { id: projectId } },
      })
      return res.data
    },
    onSuccess: (data) => {
      if (data && 'marcas' in data && Array.isArray(data.marcas)) {
        setMarcasEstudio(data.marcas as BrandItem[])
      }
    },
  })

  // Mutación proponer prompts (Paso 3 vivo)
  const mutProposePrompts = useMutation({
    mutationFn: async () => {
      if (!projectId) return null
      const res = await api.POST('/projects/{id}/study/prompts/propose', {
        params: { path: { id: projectId } },
      })
      return res.data
    },
    onSuccess: (data) => {
      if (data && 'prompts' in data && Array.isArray(data.prompts)) {
        setPromptsEstudio(data.prompts)
      }
    },
  })

  // Mutación lanzar (Paso 4)
  const mutLanzar = useMutation({
    mutationFn: async () => {
      if (!projectId) return null
      // Actualizar revisión
      await api.PATCH('/projects/{id}', {
        params: { path: { id: projectId } },
        body: { revision },
      })
      // Lanzar
      const res = await api.POST('/projects/{id}/run', {
        params: { path: { id: projectId } },
        body: { confirmo_coste: confirmoCoste },
      })
      return res.data
    },
    onSuccess: () => {
      if (projectId) navigate(`/proyectos/${projectId}`)
    },
  })

  const costeTotal = estimacionTotal?.total_eur ?? 0

  return (
    <div className="grid max-w-4xl gap-6">
      <PageHeader
        title="Nuevo análisis"
        description="Asistente de configuración de proyecto, datos del estudio y parámetros de ejecución."
      />

      {/* Indicador de 4 pasos */}
      <div className="flex items-center justify-between border-b border-[var(--border)] pb-4 text-xs font-medium">
        {[
          { num: 1, label: 'Tipo y nombre' },
          { num: 2, label: tipo === 'cliente' ? 'Brief' : 'Marca prospecto' },
          { num: 3, label: 'Datos del estudio' },
          { num: 4, label: 'Ejecución' },
        ].map((s) => (
          <div
            key={s.num}
            className={`flex items-center gap-2 ${
              paso === s.num
                ? 'font-bold text-[var(--brand-project)]'
                : paso > s.num
                ? 'text-[var(--good)]'
                : 'text-[var(--fg-muted)]'
            }`}
          >
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                paso === s.num
                  ? 'bg-[var(--brand-project)] text-white'
                  : paso > s.num
                  ? 'bg-[var(--good)] text-white'
                  : 'bg-[var(--surface-2)] text-[var(--fg-muted)]'
              }`}
            >
              {paso > s.num ? '✓' : s.num}
            </span>
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      {/* PASO 1 · Tipo de análisis */}
      {paso === 1 && (
        <Panel title="Paso 1 · Tipo de análisis y nombre">
          <div className="grid gap-5">
            <div className="grid gap-2">
              <label className="text-xs font-semibold">Tipo de análisis</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setTipo('cliente')}
                  className={`rounded border p-4 text-left transition-all ${
                    tipo === 'cliente'
                      ? 'border-[var(--brand-project)] bg-[var(--brand-project)]/5'
                      : 'border-[var(--border)] hover:bg-[var(--surface-2)]'
                  }`}
                >
                  <div className="font-semibold text-sm">Cliente (tengo su brief)</div>
                  <div className="mt-1 text-xs text-[var(--fg-muted)]">
                    Auditoría exhaustiva con presupuesto, objetivos, ficha completa y plan de acción.
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setTipo('prospecto')}
                  className={`rounded border p-4 text-left transition-all ${
                    tipo === 'prospecto'
                      ? 'border-[var(--brand-project)] bg-[var(--brand-project)]/5'
                      : 'border-[var(--border)] hover:bg-[var(--surface-2)]'
                  }`}
                >
                  <div className="font-semibold text-sm">Prospecto (sin brief)</div>
                  <div className="mt-1 text-xs text-[var(--fg-muted)]">
                    Diagnóstico ágil, 3 oportunidades clave y propuesta comercial redactada.
                  </div>
                </button>
              </div>
            </div>

            <div className="grid gap-1.5">
              <label className="text-xs font-semibold">Nombre del proyecto</label>
              <Input
                placeholder="Ej. Auditoría GEO · Clínica Alborada"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
              />
            </div>

            <div className="flex justify-end pt-2">
              <Button
                variant="primary"
                disabled={mutCrear.isPending}
                onClick={() => mutCrear.mutate()}
              >
                {mutCrear.isPending ? 'Creando borrador...' : 'Continuar al paso 2'}
              </Button>
            </div>
          </div>
        </Panel>
      )}

      {/* PASO 2 · Brief o Prospecto */}
      {paso === 2 && (
        <Panel title={tipo === 'cliente' ? 'Paso 2 · Brief del cliente' : 'Paso 2 · Datos de la marca prospecto'}>
          <div className="grid gap-5">
            {tipo === 'cliente' ? (
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <label className="text-xs font-semibold">
                    Subir archivo (.md, .txt, .docx, .pdf) o pegar texto del brief
                  </label>
                  <div className="flex items-center gap-3">
                    <input
                      type="file"
                      accept=".md,.txt,.docx,.pdf"
                      onChange={async (e) => {
                        const file = e.target.files?.[0]
                        if (file && projectId) {
                          const formData = new FormData()
                          formData.append('archivo', file)
                          const res = await fetch(`/api/projects/${projectId}/brief`, {
                            method: 'POST',
                            body: formData,
                          })
                          const data = await res.json()
                          if (data) setFichaPreview(data)
                        }
                      }}
                      className="text-xs text-[var(--fg-muted)]"
                    />
                  </div>
                  <Textarea
                    rows={6}
                    placeholder="Pega aquí el texto del brief si no tienes archivo..."
                    value={briefTexto}
                    onChange={(e) => setBriefTexto(e.target.value)}
                  />
                  {briefTexto && (
                    <div>
                      <Button
                        size="sm"
                        variant="default"
                        disabled={mutBrief.isPending}
                        onClick={() => mutBrief.mutate(briefTexto)}
                      >
                        {mutBrief.isPending ? 'Extrayendo ficha...' : 'Interpretar texto'}
                      </Button>
                    </div>
                  )}
                </div>

                {fichaPreview?.ficha && (
                  <div className="rounded border border-[var(--border)] bg-[var(--surface-2)] p-4 text-xs">
                    <h4 className="font-semibold mb-2">Vista previa de la ficha extraída</h4>
                    <div className="grid grid-cols-2 gap-2 text-[var(--fg)]">
                      <div>Marca: <strong>{fichaPreview.ficha.marca || '—'}</strong></div>
                      <div>Sector: <strong>{fichaPreview.ficha.sector || '—'}</strong></div>
                      <div>Ciudades: <strong>{fichaPreview.ficha.ciudades?.join(', ') || '—'}</strong></div>
                      <div>Objetivo: <strong>{fichaPreview.ficha.objetivo_principal || '—'}</strong></div>
                    </div>
                    {fichaPreview.faltantes && fichaPreview.faltantes.length > 0 && (
                      <div className="mt-2 text-[var(--warn)]">
                        Campos pendientes: {fichaPreview.faltantes.join(', ')}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="grid gap-1">
                  <label className="text-xs font-medium">Marca *</label>
                  <Input value={prospectMarca} onChange={(e) => setProspectMarca(e.target.value)} placeholder="Ej. Urbanika Dental" />
                </div>
                <div className="grid gap-1">
                  <label className="text-xs font-medium">Dominio web *</label>
                  <Input value={prospectDominio} onChange={(e) => setProspectDominio(e.target.value)} placeholder="urbanikadental.example" />
                </div>
                <div className="grid gap-1">
                  <label className="text-xs font-medium">Sector *</label>
                  <Input value={prospectSector} onChange={(e) => setProspectSector(e.target.value)} placeholder="Clínica dental" />
                </div>
                <div className="grid gap-1">
                  <label className="text-xs font-medium">Ciudad principal *</label>
                  <Input value={prospectCiudad} onChange={(e) => setProspectCiudad(e.target.value)} placeholder="Valencia" />
                </div>
                <div className="sm:col-span-2 grid gap-1">
                  <label className="text-xs font-medium">Competidores conocidos (uno por línea)</label>
                  <Textarea rows={3} value={prospectCompetidores} onChange={(e) => setProspectCompetidores(e.target.value)} placeholder="Dentix&#10;Vitaldent" />
                </div>
              </div>
            )}

            <div className="flex justify-between pt-2">
              <Button variant="ghost" onClick={() => setPaso(1)}>Atrás</Button>
              <Button
                variant="primary"
                onClick={async () => {
                  if (tipo === 'prospecto') {
                    await mutProspect.mutateAsync()
                  }
                  setPaso(3)
                }}
              >
                Continuar al paso 3
              </Button>
            </div>
          </div>
        </Panel>
      )}

      {/* PASO 3 · Datos del estudio */}
      {paso === 3 && (
        <Panel title="Paso 3 · Datos del estudio">
          <div className="grid gap-5">
            <div className="flex border-b border-[var(--border)] pb-2 text-xs font-medium gap-4">
              <button
                type="button"
                onClick={() => setPestanaDatos('csv')}
                className={`pb-1 ${pestanaDatos === 'csv' ? 'border-b-2 border-[var(--brand-project)] font-bold text-[var(--brand-project)]' : 'text-[var(--fg-muted)]'}`}
              >
                a) Subir datos del estudio (CSV del kit)
              </button>
              <button
                type="button"
                onClick={() => setPestanaDatos('vivo')}
                className={`pb-1 ${pestanaDatos === 'vivo' ? 'border-b-2 border-[var(--brand-project)] font-bold text-[var(--brand-project)]' : 'text-[var(--fg-muted)]'}`}
              >
                b) Generar estudio en vivo con IA
              </button>
            </div>

            {pestanaDatos === 'csv' ? (
              <div className="grid gap-4">
                <div className="rounded border-2 border-dashed border-[var(--border)] p-6 text-center">
                  <p className="text-xs text-[var(--fg-muted)] mb-3">
                    Arrastra aquí los archivos CSV del estudio (ejecuciones.csv, marcas.csv, banco_prompts.csv) o selecciónalos:
                  </p>
                  <input
                    type="file"
                    multiple
                    accept=".csv"
                    onChange={(e) => e.target.files && mutUpload.mutate(e.target.files)}
                    className="text-xs text-[var(--fg-muted)]"
                  />
                </div>

                {uploadReports.length > 0 && (
                  <div className="grid gap-2 text-xs">
                    <h4 className="font-semibold">Informe de validación por archivo</h4>
                    {uploadReports.map((r, i) => (
                      <div
                        key={i}
                        className={`rounded border p-2.5 flex items-center justify-between ${
                          r.errores && r.errores.length > 0 ? 'border-[var(--bad)]/30 bg-[var(--bad)]/5 text-[var(--bad)]' : 'border-[var(--good)]/30 bg-[var(--good)]/5'
                        }`}
                      >
                        <div>
                          <strong>{r.archivo}</strong> ({r.tipo || 'desconocido'}) — {r.filas} filas
                          {r.avisos && r.avisos.length > 0 && <span className="ml-2 text-[var(--warn)]">({r.avisos.length} avisos)</span>}
                        </div>
                        <div>{r.errores && r.errores.length > 0 ? 'Error bloqueante' : 'Válido'}</div>
                      </div>
                    ))}
                  </div>
                )}

                {studySummary && (
                  <div className="rounded border bg-[var(--surface-2)] p-3 text-xs">
                    <h4 className="font-semibold mb-1">Resumen del estudio</h4>
                    <div className="grid grid-cols-3 gap-2">
                      <div>Ejecuciones: <strong>{studySummary.ejecuciones}</strong></div>
                      <div>Motores: <strong>{studySummary.motores}</strong></div>
                      <div>Prompts: <strong>{studySummary.prompts}</strong></div>
                      <div>Marcas: <strong>{studySummary.marcas}</strong></div>
                      <div>Espontáneas: <strong>{studySummary.espontaneas}</strong></div>
                      <div>Asistidas: <strong>{studySummary.asistidas}</strong></div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="grid gap-4 text-xs">
                {!settings?.clave_configurada && (
                  <div className="rounded border border-[var(--warn)]/40 bg-[var(--warn)]/10 p-3 text-[var(--warn)]">
                    No tienes clave de OpenRouter configurada. Puedes configurarla en Ajustes para lanzar estudios en vivo.
                  </div>
                )}

                <div className="flex items-center justify-between border-b pb-3">
                  <div>
                    <h4 className="font-semibold">Marcas a monitorizar</h4>
                    <p className="text-[var(--fg-muted)]">Propuesta automática del brief y competidores relevantes.</p>
                  </div>
                  <Button size="sm" variant="default" onClick={() => mutProposeBrands.mutate()}>
                    Proponer marcas
                  </Button>
                </div>
                {marcasEstudio.length > 0 && (
                  <div className="text-[11px] text-[var(--fg-muted)]">
                    {marcasEstudio.length} marcas identificadas ({marcasEstudio.filter(m => m.nivel === 'foco').length} foco).
                  </div>
                )}

                <div className="flex items-center justify-between border-b pb-3">
                  <div>
                    <h4 className="font-semibold">Banco de prompts</h4>
                    <p className="text-[var(--fg-muted)]">Plantillas para las 9 familias de la metodología GEO.</p>
                  </div>
                  <Button size="sm" variant="default" onClick={() => mutProposePrompts.mutate()}>
                    Proponer banco
                  </Button>
                </div>
                {promptsEstudio.length > 0 && (
                  <div className="text-[11px] text-[var(--fg-muted)]">
                    {promptsEstudio.length} plantillas propuestas.
                  </div>
                )}

                <div className="grid gap-2">
                  <h4 className="font-semibold">Tamaño del estudio</h4>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { id: 'rapido', label: 'Rápido', desc: 'P1 · 2 repeticiones' },
                      { id: 'estandar', label: 'Estándar', desc: 'Todo · 2 repeticiones' },
                      { id: 'completo', label: 'Completo', desc: 'Todo · 3 repeticiones' },
                    ].map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => setTamanoEstudio(t.id as any)}
                        className={`rounded border p-2 text-left ${tamanoEstudio === t.id ? 'border-[var(--brand-project)] bg-[var(--brand-project)]/5' : 'border-[var(--border)]'}`}
                      >
                        <div className="font-medium">{t.label}</div>
                        <div className="text-[10px] text-[var(--fg-muted)]">{t.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-between pt-2">
              <Button variant="ghost" onClick={() => setPaso(2)}>Atrás</Button>
              <Button variant="primary" onClick={() => setPaso(4)}>
                Continuar al paso 4
              </Button>
            </div>
          </div>
        </Panel>
      )}

      {/* PASO 4 · Ejecución */}
      {paso === 4 && (
        <Panel title="Paso 4 · Parámetros de ejecución y lanzamiento">
          <div className="grid gap-5 text-sm">
            <div className="grid gap-2">
              <label className="text-xs font-semibold">Modo de revisión</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setRevision('pausas')}
                  className={`rounded border p-3 text-left ${revision === 'pausas' ? 'border-[var(--brand-project)] bg-[var(--brand-project)]/5 font-semibold' : 'border-[var(--border)]'}`}
                >
                  <div className="text-sm">Parar en cada punto de control</div>
                  <div className="mt-1 text-xs text-[var(--fg-muted)] font-normal">
                    Pausa tras la ficha, competencia, hallazgos y plan para validación humana.
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setRevision('continuo')}
                  className={`rounded border p-3 text-left ${revision === 'continuo' ? 'border-[var(--brand-project)] bg-[var(--brand-project)]/5 font-semibold' : 'border-[var(--border)]'}`}
                >
                  <div className="text-sm">Ejecutar del tirón</div>
                  <div className="mt-1 text-xs text-[var(--fg-muted)] font-normal">
                    Completa todo el análisis automáticamente con opción de revisión posterior.
                  </div>
                </button>
              </div>
            </div>

            <div className="rounded border bg-[var(--surface-2)] p-4 text-xs grid gap-2">
              <h4 className="font-semibold text-sm">Resumen de coste estimado</h4>
              <div className="flex justify-between">
                <span>Total de llamadas previstas:</span>
                <strong>{estimacionTotal?.total_llamadas ?? 0} llamadas</strong>
              </div>
              <div className="flex justify-between">
                <span>Tiempo estimado:</span>
                <strong>~{estimacionTotal?.minutos ?? 1} minutos</strong>
              </div>
              <div className="flex justify-between text-base font-bold text-[var(--brand-project)] border-t pt-2">
                <span>Coste previsto:</span>
                <span>{formatEur(costeTotal)}</span>
              </div>
            </div>

            {costeTotal > 0 && (
              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input
                  type="checkbox"
                  checked={confirmoCoste}
                  onChange={(e) => setConfirmoCoste(e.target.checked)}
                />
                <span>He revisado el coste estimado ({formatEur(costeTotal)}) y autorizo su consumo.</span>
              </label>
            )}

            <div className="flex justify-between pt-2">
              <Button variant="ghost" onClick={() => setPaso(3)}>Atrás</Button>
              <Button
                variant="primary"
                disabled={mutLanzar.isPending || (costeTotal > 0 && !confirmoCoste)}
                onClick={() => mutLanzar.mutate()}
              >
                {mutLanzar.isPending ? 'Lanzando análisis...' : 'Lanzar análisis'}
              </Button>
            </div>
          </div>
        </Panel>
      )}
    </div>
  )
}
