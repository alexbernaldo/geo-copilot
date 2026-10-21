import { useMemo, useState } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import type { EChartsOption } from 'echarts'
import t1 from '../mocks/fixtures/tables/T1_espontanea.json'
import t2 from '../mocks/fixtures/tables/T2.json'
import estimateFx from '../mocks/fixtures/estimates_analysis.json'
import type { Estimate } from '@/api/types'
import {
  Button, Checkbox, Chart, CheckpointBar, Chip, CostConfirm, DataTable, Dialog, Drawer, EmptyState, ErrorState, EvidenceLink, Input,
  KpiStrip, Markdown, OriginTag, PageHeader, Panel, PendingState, ScopeToggle, Select, Skeleton, Slider, SourceNote, Tabs, Textarea, Tooltip,
  useBrandColors, heatRamp, type Scope, type Tone,
} from '@/components'
import { formatEur, formatNum, formatPct } from '@/lib/format'
import { cssVar, useTheme } from '@/lib/theme'

interface Fila { marca: string; motor?: string; n: number; tasa_aparicion: number; score: number; puesto?: number }
const T1 = (t1.filas as unknown as Fila[]).slice().sort((a, b) => b.score - a.score)
const T2 = t2.filas as unknown as Fila[]
const MARCA = 'Clínica Alborada Visión'
const LIDER = 'Grupo Hospitalario Valdecruz'
const LONG = 'Centro Internacional de Oftalmología Avanzada y Cirugía Refractiva del Mediterráneo Occidental S.L.U.'
const TONES: Tone[] = ['neutral', 'good', 'warn', 'bad', 'info', 'spont', 'assist', 'accent']

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: 16, alignItems: 'start', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <div style={{ color: 'var(--fg-muted)', fontSize: 'var(--text-sm)', paddingTop: 4 }}>{label}</div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center', minWidth: 0 }}>{children}</div>
    </div>
  )
}

/** Página /_kit (solo en desarrollo): todos los componentes compartidos en sus estados. */
export default function KitPage() {
  const [scope, setScope] = useState<Scope>('espontanea')
  const [worst, setWorst] = useState(false)
  const [dlg, setDlg] = useState(false)
  const [drw, setDrw] = useState(false)
  const [sel, setSel] = useState('chatgpt')
  const [chk, setChk] = useState(true)
  const [sl, setSl] = useState(40)
  const [confirm, setConfirm] = useState(false)
  const { resolved, setChoice } = useTheme()
  const color = useBrandColors(MARCA, LIDER)

  const rows = useMemo(() => T1.map((r) => (worst ? { ...r, marca: r === T1[0] ? LONG : r.marca } : r)), [worst])
  const many = useMemo(() => Array.from({ length: 3000 }, (_, i) => ({ id: `EJ-${String(i + 1).padStart(4, '0')}`, marca: T1[i % T1.length]!.marca, score: (i * 7) % 100 })), [])
  const estimate: Estimate = estimateFx as Estimate
  const over: Estimate = { ...estimate, total_eur: 21.4, supera_tope: true }

  const cols: ColumnDef<Fila, unknown>[] = [
    { accessorKey: 'puesto', header: 'Puesto', meta: { numeric: true }, cell: (c) => c.row.index + 1 },
    { accessorKey: 'marca', header: 'Marca', cell: (c) => { const m = String(c.getValue()); const mine = m === MARCA || m === LIDER; return <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontWeight: mine ? 600 : 400 }}><i aria-hidden style={{ width: 8, height: 8, borderRadius: 2, background: color(m), flex: 'none' }} />{m}</span> } },
    { accessorKey: 'n', header: 'n', meta: { numeric: true }, cell: (c) => formatNum(Number(c.getValue())) },
    { accessorKey: 'tasa_aparicion', header: 'Aparición', meta: { numeric: true }, cell: (c) => formatPct(Number(c.getValue()) * 100) },
    { accessorKey: 'score', header: 'Score', meta: { numeric: true }, cell: (c) => formatNum(Number(c.getValue()), 1) },
  ]
  const idCols: ColumnDef<(typeof many)[number], unknown>[] = [
    { accessorKey: 'id', header: 'Ejecución', cell: (c) => <span className="num">{String(c.getValue())}</span> },
    { accessorKey: 'marca', header: 'Marca' },
    { accessorKey: 'score', header: 'Score', meta: { numeric: true } },
  ]

  const ranking: EChartsOption = {
    grid: { left: 8, right: 40, top: 8, bottom: 8, containLabel: true },
    xAxis: { type: 'value', max: 100 },
    yAxis: { type: 'category', inverse: true, data: rows.map((r) => r.marca), axisLabel: { width: 190, overflow: 'truncate' } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    series: [{ type: 'bar', barWidth: 14, data: rows.map((r) => ({ value: Number(r.score.toFixed(1)), itemStyle: { color: color(r.marca), borderRadius: [0, 3, 3, 0] } })), label: { show: true, position: 'right', fontFamily: cssVar('--font-mono'), color: cssVar('--fg'), formatter: (p) => formatNum(Number(p.value), 1) } }],
  }
  const marcas = T1.map((r) => r.marca)
  const motores = ['ChatGPT', 'Gemini', 'Perplexity', 'Claude']
  const heat: EChartsOption = {
    grid: { left: 8, right: 16, top: 8, bottom: 56, containLabel: true },
    tooltip: { formatter: (p: unknown) => { const d = (p as { data: { value: [number, number, number] } }).data.value; return `${marcas[d[1]]} · ${motores[d[0]]}: ${formatPct(d[2])}` } },
    xAxis: { type: 'category', data: motores, splitArea: { show: false } },
    yAxis: { type: 'category', inverse: true, data: marcas, axisLabel: { width: 190, overflow: 'truncate' } },
    visualMap: { min: 0, max: 100, calculable: false, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: heatRamp() } },
    series: [{ type: 'heatmap', data: T2.filter((r) => marcas.includes(r.marca)).map((r) => { const v = Number((r.tasa_aparicion * 100).toFixed(1)); return { value: [motores.indexOf(r.motor ?? ''), marcas.indexOf(r.marca), v], label: { color: v > 50 ? '#ffffff' : cssVar('--fg') } } }), label: { show: true, fontFamily: cssVar('--font-mono'), fontSize: 11, formatter: (p) => formatNum(Number((p.value as number[])[2]), 0) }, itemStyle: { borderColor: 'transparent', borderWidth: 2 } }],
  }
  const tableFb = (
    <DataTable columns={cols} data={rows} caption="Ranking de marcas por score espontáneo" />
  )

  return (
    <div style={{ display: 'grid', gap: 8 }}>
      <PageHeader
        title="Kit de componentes"
        description="Todos los componentes compartidos en sus estados. Solo en desarrollo. Los datos salen de las fixtures; ninguna cifra se calcula aquí."
        checkpoint={{ n: 1, approved: false }}
        actions={
          <>
            <Checkbox checked={worst} onCheckedChange={setWorst} label="Peor caso (datos extremos)" />
            <Button onClick={() => setChoice(resolved === 'dark' ? 'light' : 'dark')}>{resolved === 'dark' ? 'Tema claro' : 'Tema oscuro'}</Button>
          </>
        }
      />

      <Panel title="Identidad: color de datos" source={<SourceNote tabla="DESIGN.md" n={5} />}>
        <Row label="Marca, líder, resto">
          <Chip tone="accent" dot>Marca del proyecto</Chip><span style={{ color: 'var(--brand-leader)', fontWeight: 600 }}>Líder del mercado</span><span style={{ color: 'var(--fg-muted)' }}>Resto de marcas (gris neutro)</span>
        </Row>
        <Row label="Ámbito"><Chip tone="spont" dot>Espontánea</Chip><Chip tone="assist" dot>Asistida</Chip></Row>
        <Row label="Chips">{TONES.map((t) => <Chip key={t} tone={t}>{t}</Chip>)}</Row>
        <Row label="Origen"><OriginTag origen="calculado" /><OriginTag origen="ia" modelo="anthropic/claude-sonnet-4.5" /><OriginTag origen="automatico" /><OriginTag origen="editado" /></Row>
      </Panel>

      <Panel title="Botones y campos">
        <Row label="Botón"><Button variant="primary">Primario</Button><Button>Secundario</Button><Button variant="ghost">Fantasma</Button><Button variant="danger">Borrar proyecto</Button><Button size="sm">Pequeño</Button></Row>
        <Row label="Estados"><Button disabled>Deshabilitado</Button><Button loading variant="primary">Lanzando</Button></Row>
        <Row label="Entrada"><div style={{ width: 240 }}><Input aria-label="Nombre" placeholder="Nombre del proyecto" /></div><div style={{ width: 240 }}><Input aria-label="Con error" defaultValue="Valor no válido" invalid /></div><div style={{ width: 240 }}><Input aria-label="Deshabilitado" disabled defaultValue="No editable" /></div></Row>
        <Row label="Área de texto"><div style={{ width: 420 }}><Textarea aria-label="Notas" placeholder="Pega aquí el brief" /></div></Row>
        <Row label="Selector"><div style={{ width: 240 }}><Select ariaLabel="Motor" value={sel} onValueChange={setSel} options={[{ value: 'chatgpt', label: 'ChatGPT' }, { value: 'gemini', label: 'Gemini' }, { value: 'perplexity', label: 'Perplexity' }, { value: 'claude', label: 'Claude' }]} /></div></Row>
        <Row label="Casilla"><Checkbox checked={chk} onCheckedChange={setChk} label="He revisado el coste estimado" /><Checkbox checked={false} onCheckedChange={() => {}} label="Deshabilitada" disabled /></Row>
        <Row label="Deslizador"><div style={{ width: 280 }}><Slider ariaLabel="Aparición" value={sl} onValueChange={setSl} /></div><span className="num">{formatPct(sl, 0)}</span></Row>
        <Row label="Pista"><Tooltip content="Origen: T2 · n=60"><Button>Pasa el ratón o enfoca</Button></Tooltip><SourceNote tabla="T2" n={60} /></Row>
      </Panel>

      <Panel title="Navegación y capas">
        <Row label="Pestañas"><div style={{ width: '100%' }}><Tabs items={[{ value: 'a', label: 'Subir datos del estudio', content: <p>Contenido de la primera pestaña.</p> }, { value: 'b', label: 'Generar en vivo', content: <p>Contenido de la segunda pestaña.</p> }]} /></div></Row>
        <Row label="Diálogo y cajón"><Button onClick={() => setDlg(true)}>Abrir diálogo</Button><Button onClick={() => setDrw(true)}>Abrir cajón</Button><EvidenceLink ids={['EJ-0001', 'EJ-0002']} /></Row>
      </Panel>
      <Dialog open={dlg} onOpenChange={setDlg} title="Borrar proyecto" description="Escribe el nombre del proyecto para confirmar. Esta acción no se puede deshacer.">
        <div style={{ marginTop: 16, display: 'grid', gap: 12 }}><Input aria-label="Nombre para confirmar" placeholder={MARCA} /><div className="cost-actions"><Button onClick={() => setDlg(false)}>Cancelar</Button><Button variant="danger">Borrar</Button></div></div>
      </Dialog>
      <Drawer open={drw} onOpenChange={setDrw} title="Ejecución EJ-0001" description="Detalle con respuesta, fuentes y evaluación por marca.">
        <Markdown source={'### Respuesta\n\nLas **clínicas** más citadas en Madrid son...\n\n| Marca | Posición |\n|---|---|\n| Valdecruz | 1 |'} />
      </Drawer>

      <Panel title="Cifras" source={<ScopeToggle value={scope} onChange={setScope} />}>
        <KpiStrip scope={scope} items={[
          { label: 'Score', value: '27,97', unit: '/ 100', note: 'Puesto 7 de 10', source: <SourceNote tabla="T1" n={240} />, highlight: true },
          { label: 'Aparición', value: formatPct(38.75), source: <SourceNote tabla="T1" n={240} /> },
          { label: 'Recomendación activa', value: formatPct(6.67), note: 'Líder: 34,6 %' },
          { label: worst ? LONG : 'Coste del plan', value: formatEur(24300), note: worst ? 'Sobre un presupuesto máximo de 99.999.999 €' : 'Dentro del presupuesto' },
        ]} />
      </Panel>

      <Panel title="Estados">
        <Row label="Vacío"><EmptyState title="Aún no hay proyectos" description="Crea un proyecto con el brief de una marca y los datos de su estudio." action={<Button variant="primary">Nuevo proyecto</Button>} /></Row>
        <Row label="Pendiente"><PendingState step="Hallazgos" /></Row>
        <Row label="Error"><ErrorState error={{ error: { code: 'llm', message: 'OpenRouter ha respondido con un límite de peticiones. Espera un minuto y reintenta.' } }} onRetry={() => {}} /></Row>
        <Row label="Cargando"><div style={{ width: 360, display: 'grid', gap: 8 }}><Skeleton height={20} width="50%" /><Skeleton height={80} /></div></Row>
      </Panel>

      <CheckpointBar n={1} approved={false} onApprove={() => {}} summary="10 marcas en el estudio; 2 avisos de discrepancia entre el brief y los datos." />
      <CheckpointBar n={0} approved onApprove={() => {}} summary="Ficha revisada y aprobada." />

      <Panel title="Coste antes de gastar">
        <Row label="Estimación"><Button onClick={() => setConfirm((c) => !c)}>{confirm ? 'Ocultar' : 'Mostrar confirmación'}</Button></Row>
        {confirm && <CostConfirm estimate={estimate} onConfirm={() => setConfirm(false)} onCancel={() => setConfirm(false)} />}
        <div style={{ marginTop: 16 }}><CostConfirm estimate={over} onConfirm={() => {}} onCancel={() => {}} /></div>
      </Panel>

      <Panel title="Tabla" source={<SourceNote tabla="T1" n={240} />}>
        <DataTable columns={cols} data={rows} caption="Ranking de marcas" />
      </Panel>
      <Panel title="Tabla con 3.000 filas (se pagina en cliente)">
        <DataTable columns={idCols} data={many} pageSize={50} caption="Ejecuciones" />
      </Panel>
      <Panel title="Tabla vacía"><DataTable columns={cols} data={[]} emptyText="Ninguna ejecución coincide con los filtros." /></Panel>

      <Panel title="Gráficos (tema ECharts de los tokens)" source={<OriginTag origen="calculado" />}>
        <Chart ariaLabel="Ranking de marcas por score espontáneo. La marca del proyecto es la azul y el líder la naranja." option={ranking} height={worst ? 360 : 320} tableFallback={tableFb} />
        <Chart ariaLabel="Mapa de calor de aparición espontánea por marca y motor." option={heat} height={420} />
      </Panel>

      <Panel title="Markdown"><Markdown source={'## Resumen ejecutivo\n\nLa marca aparece en el **38,8 %** de las respuestas espontáneas (n=240).\n\n- Primer hallazgo\n- Segundo hallazgo\n\n| Motor | Aparición |\n|---|---|\n| ChatGPT | 40,0 % |'} /></Panel>
    </div>
  )
}
