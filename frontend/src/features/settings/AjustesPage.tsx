import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Input, PageHeader, Panel } from '@/components'
import { api } from '@/api/client'
import { formatEur } from '@/lib/format'
import type { components } from '@/api/schema'

type SettingsTest = components['schemas']['SettingsTest']

export default function AjustesPage() {
  const queryClient = useQueryClient()
  const [clave, setClave] = useState('')
  const [testResult, setTestResult] = useState<SettingsTest | null>(null)

  // Roles de modelos
  const [juez, setJuez] = useState('')
  const [redaccion, setRedaccion] = useState('')
  const [propuesta, setPropuesta] = useState('')
  const [chatgpt, setChatgpt] = useState('')
  const [gemini, setGemini] = useState('')
  const [claude, setClaude] = useState('')
  const [perplexity, setPerplexity] = useState('')

  // Límites
  const [concurrencia, setConcurrencia] = useState(8)
  const [maxLlamadas, setMaxLlamadas] = useState(1500)
  const [topeGastoEur, setTopeGastoEur] = useState(5.0)
  const [usdEur, setUsdEur] = useState(0.92)

  const [guardado, setGuardado] = useState(false)

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => {
      const res = await api.GET('/settings', {})
      return res.data
    },
  })

  useEffect(() => {
    if (settings) {
      if (settings.modelos) {
        setJuez(settings.modelos.juez || '')
        setRedaccion(settings.modelos.redaccion || '')
        setPropuesta(settings.modelos.propuesta || '')
        setChatgpt(settings.modelos.chatgpt || '')
        setGemini(settings.modelos.gemini || '')
        setClaude(settings.modelos.claude || '')
        setPerplexity(settings.modelos.perplexity || '')
      }
      if (settings.limites) {
        setConcurrencia(settings.limites.concurrencia)
        setMaxLlamadas(settings.limites.max_llamadas)
        setTopeGastoEur(settings.limites.tope_gasto_eur)
        setUsdEur(settings.limites.usd_eur)
      }
    }
  }, [settings])

  const mutSave = useMutation({
    mutationFn: async () => {
      await api.PUT('/settings', {
        body: {
          clave: clave.trim() ? clave.trim() : undefined,
          modelos: {
            juez: juez.trim() || undefined,
            redaccion: redaccion.trim() || undefined,
            propuesta: propuesta.trim() || undefined,
            chatgpt: chatgpt.trim() || undefined,
            gemini: gemini.trim() || undefined,
            claude: claude.trim() || undefined,
            perplexity: perplexity.trim() || undefined,
          },
          limites: {
            concurrencia: Number(concurrencia),
            max_llamadas: Number(maxLlamadas),
            tope_gasto_eur: Number(topeGastoEur),
            usd_eur: Number(usdEur),
          },
        },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      setClave('')
      setGuardado(true)
      setTimeout(() => setGuardado(false), 3000)
    },
  })

  const mutTest = useMutation({
    mutationFn: async () => {
      const res = await api.POST('/settings/test', {})
      return res.data
    },
    onSuccess: (data) => {
      setTestResult(data ?? null)
    },
  })

  if (isLoading) {
    return (
      <div className="grid gap-6">
        <PageHeader title="Ajustes" description="Configuración global del sistema." />
        <Panel><div className="py-8 text-center text-sm text-[var(--fg-muted)]">Cargando ajustes...</div></Panel>
      </div>
    )
  }

  return (
    <div className="grid max-w-4xl gap-6">
      <PageHeader
        title="Ajustes"
        description="Configuración global de OpenRouter, modelos por función, topes de gasto y almacenamiento."
        actions={
          <div className="flex items-center gap-3">
            {guardado && <span className="text-xs text-[var(--good)]">Ajustes guardados correctamente</span>}
            <Button
              variant="primary"
              disabled={mutSave.isPending}
              onClick={() => mutSave.mutate()}
            >
              {mutSave.isPending ? 'Guardando...' : 'Guardar cambios'}
            </Button>
          </div>
        }
      />

      {/* 1. Conexión OpenRouter */}
      <Panel title="Conexión con OpenRouter">
        <div className="grid gap-4">
          <div className="grid gap-1.5">
            <label className="text-xs font-medium text-[var(--fg)]">
              Clave de API de OpenRouter
            </label>
            <div className="flex items-center gap-3">
              <Input
                type="password"
                placeholder={settings?.clave_mascara || 'sk-or-v1-...'}
                value={clave}
                onChange={(e) => setClave(e.target.value)}
                className="flex-1 font-mono text-sm"
              />
              <Button
                variant="default"
                disabled={mutTest.isPending}
                onClick={() => mutTest.mutate()}
              >
                {mutTest.isPending ? 'Probando...' : 'Probar conexión'}
              </Button>
            </div>
            <p className="text-xs text-[var(--fg-muted)]">
              {settings?.clave_configurada ? (
                <span>Clave activa configurada ({settings.clave_mascara}). Introduce un nuevo valor para sustituirla.</span>
              ) : (
                <span>No hay clave configurada. Los análisis se ejecutarán con los datos base del estudio.</span>
              )}{' '}
              <a
                href="https://openrouter.ai/keys"
                target="_blank"
                rel="noreferrer"
                className="underline hover:text-[var(--brand-project)]"
              >
                Obtener clave en openrouter.ai
              </a>
            </p>
          </div>

          {testResult && (
            <div
              className={`rounded border p-3 text-xs ${
                testResult.ok
                  ? 'border-[var(--good)]/30 bg-[var(--good)]/10 text-[var(--fg)]'
                  : 'border-[var(--bad)]/30 bg-[var(--bad)]/10 text-[var(--bad)]'
              }`}
            >
              <div className="font-semibold">{testResult.mensaje}</div>
              {testResult.ok && (
                <div className="mt-1 flex flex-wrap gap-4 text-[var(--fg-muted)]">
                  {testResult.latencia_ms && <span>Latencia: {testResult.latencia_ms} ms</span>}
                  {testResult.coste_eur !== undefined && testResult.coste_eur !== null && <span>Coste prueba: {formatEur(testResult.coste_eur)}</span>}
                  {testResult.gasto_clave_usd !== undefined && testResult.gasto_clave_usd !== null && <span>Gasto acumulado: ${testResult.gasto_clave_usd}</span>}
                  {testResult.limite_clave_usd !== undefined && testResult.limite_clave_usd !== null && <span>Límite de la clave: ${testResult.limite_clave_usd}</span>}
                </div>
              )}
            </div>
          )}
        </div>
      </Panel>

      {/* 2. Modelos por rol */}
      <Panel title="Modelos por función">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="grid gap-1.5">
            <label className="text-xs font-medium">Juez, extracción y revisor</label>
            <Input
              value={juez}
              onChange={(e) => setJuez(e.target.value)}
              placeholder="google/gemini-2.5-flash"
              className="text-xs"
            />
          </div>
          <div className="grid gap-1.5">
            <label className="text-xs font-medium">Estrategia y redacción final</label>
            <Input
              value={redaccion}
              onChange={(e) => setRedaccion(e.target.value)}
              placeholder="anthropic/claude-sonnet-4.5"
              className="text-xs"
            />
          </div>
          <div className="grid gap-1.5 sm:col-span-2">
            <label className="text-xs font-medium">Propuesta de marcas y banco de prompts</label>
            <Input
              value={propuesta}
              onChange={(e) => setPropuesta(e.target.value)}
              placeholder="google/gemini-2.5-flash"
              className="text-xs"
            />
          </div>

          <div className="sm:col-span-2 pt-2 border-t border-[var(--border)]">
            <h4 className="text-xs font-semibold mb-3">Motores para el estudio en vivo</h4>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="grid gap-1">
                <label className="text-xs text-[var(--fg-muted)]">ChatGPT</label>
                <Input value={chatgpt} onChange={(e) => setChatgpt(e.target.value)} placeholder="openai/gpt-4o" className="text-xs" />
              </div>
              <div className="grid gap-1">
                <label className="text-xs text-[var(--fg-muted)]">Gemini</label>
                <Input value={gemini} onChange={(e) => setGemini(e.target.value)} placeholder="google/gemini-2.5-flash" className="text-xs" />
              </div>
              <div className="grid gap-1">
                <label className="text-xs text-[var(--fg-muted)]">Claude</label>
                <Input value={claude} onChange={(e) => setClaude(e.target.value)} placeholder="anthropic/claude-3.5-sonnet" className="text-xs" />
              </div>
              <div className="grid gap-1">
                <label className="text-xs text-[var(--fg-muted)]">Perplexity</label>
                <Input value={perplexity} onChange={(e) => setPerplexity(e.target.value)} placeholder="perplexity/sonar" className="text-xs" />
              </div>
            </div>
          </div>
        </div>
      </Panel>

      {/* 3. Límites y presupuesto */}
      <Panel title="Límites y control de gasto">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="grid gap-1.5">
            <label className="text-xs font-medium">Tope de gasto por proyecto (€)</label>
            <Input
              type="number"
              step="0.5"
              value={topeGastoEur}
              onChange={(e) => setTopeGastoEur(Number(e.target.value))}
              className="text-xs"
            />
            <span className="text-[10px] text-[var(--fg-muted)]">Bloquea la ejecución si la estimación o el gasto superan este valor.</span>
          </div>
          <div className="grid gap-1.5">
            <label className="text-xs font-medium">Llamadas máximas a la API</label>
            <Input
              type="number"
              value={maxLlamadas}
              onChange={(e) => setMaxLlamadas(Number(e.target.value))}
              className="text-xs"
            />
            <span className="text-[10px] text-[var(--fg-muted)]">Tope de seguridad por proyecto para evitar bucles.</span>
          </div>
          <div className="grid gap-1.5">
            <label className="text-xs font-medium">Concurrencia de llamadas simultáneas</label>
            <Input
              type="number"
              value={concurrencia}
              onChange={(e) => setConcurrencia(Number(e.target.value))}
              className="text-xs"
            />
          </div>
          <div className="grid gap-1.5">
            <label className="text-xs font-medium">Tipo de cambio USD / EUR</label>
            <Input
              type="number"
              step="0.01"
              value={usdEur}
              onChange={(e) => setUsdEur(Number(e.target.value))}
              className="text-xs"
            />
          </div>
        </div>
      </Panel>

      {/* 4. Almacenamiento */}
      <Panel title="Carpeta de datos">
        <div className="grid gap-2">
          <label className="text-xs font-medium">Ruta de proyectos en disco</label>
          <Input
            value={settings?.carpeta_datos || ''}
            readOnly
            className="bg-[var(--surface-2)] text-xs font-mono"
          />
          <p className="text-[11px] text-[var(--fg-muted)]">
            Todos los proyectos se almacenan localmente como archivos JSON y Parquet en esta ubicación.
          </p>
        </div>
      </Panel>
    </div>
  )
}
