import { delay, http, HttpResponse, sse } from 'msw'
import projects from './fixtures/projects.json'
import project from './fixtures/project.json'
import progress from './fixtures/progress.json'
import ficha from './fixtures/ficha.json'
import market from './fixtures/market.json'
import findings from './fixtures/findings.json'
import plan from './fixtures/plan.json'
import diagnosisEsp from './fixtures/diagnosis_espontanea.json'
import diagnosisAsi from './fixtures/diagnosis_asistida.json'
import executions from './fixtures/executions.json'
import executionDetail from './fixtures/execution_detail.json'
import proposal from './fixtures/proposal.json'
import quality from './fixtures/quality.json'
import traces from './fixtures/traces.json'
import settings from './fixtures/settings.json'
import models from './fixtures/models.json'
import estimatesAnalysis from './fixtures/estimates_analysis.json'
import estimatesStudy from './fixtures/estimates_study.json'
import studySummary from './fixtures/study_summary.json'
import studyConfig from './fixtures/study_config.json'
import brands from './fixtures/brands.json'
import prompts from './fixtures/prompts.json'
import instances from './fixtures/instances.json'
import health from './fixtures/health.json'

const tables = import.meta.glob('./fixtures/tables/*.json', { eager: true, import: 'default' }) as Record<string, unknown>
const A = '/api'
type SseEvents = { snapshot: unknown; step: unknown; counter: unknown; cost: unknown; checkpoint: unknown; done: unknown }

/** Secuencia simulada de un trabajo (solo desarrollo): una vez lanzado, /events emite los pasos del análisis. */
let running = false

const STEPS = ['intake', 'market', 'detect', 'judge', 'metrics', 'findings', 'plan', 'review', 'write', 'export']

export const handlers = [
  http.get(`${A}/health`, () => HttpResponse.json(health)),
  http.get(`${A}/settings`, () => HttpResponse.json(settings)),
  http.put(`${A}/settings`, () => HttpResponse.json(settings)),
  http.post(`${A}/settings/test`, () => HttpResponse.json({ ok: true, latencia_ms: 420, coste_eur: 0.0001, gasto_clave_usd: 1.2, limite_clave_usd: 20, mensaje: 'Conexión correcta.' })),
  http.get(`${A}/settings/models`, () => HttpResponse.json(models)),
  http.get(`${A}/projects`, () => HttpResponse.json(projects)),
  http.post(`${A}/projects`, () => HttpResponse.json({ ...project, estado: 'borrador', checkpoints: { ficha: false, competencia: false, hallazgos: false, plan: false } }, { status: 201 })),
  http.get(`${A}/projects/:id`, () => HttpResponse.json(project)),
  http.patch(`${A}/projects/:id`, () => HttpResponse.json(project)),
  http.delete(`${A}/projects/:id`, () => new HttpResponse(null, { status: 204 })),
  http.post(`${A}/projects/:id/duplicate`, () => HttpResponse.json(project, { status: 201 })),
  http.post(`${A}/projects/:id/brief`, () => HttpResponse.json({ ficha: ficha.ficha, faltantes: ficha.faltantes, origen_campos: {} })),
  http.post(`${A}/projects/:id/prospect`, () => HttpResponse.json({ ficha: ficha.ficha, faltantes: [], origen_campos: {} })),
  http.post(`${A}/projects/:id/study/upload`, () => HttpResponse.json({ informes: [], resumen: studySummary, bloqueado: false })),
  http.get(`${A}/projects/:id/study/summary`, () => HttpResponse.json(studySummary)),
  http.post(`${A}/projects/:id/study/brands/propose`, async () => { await delay(300); return HttpResponse.json(brands) }),
  http.get(`${A}/projects/:id/study/brands`, () => HttpResponse.json(brands)),
  http.put(`${A}/projects/:id/study/brands`, () => HttpResponse.json(brands)),
  http.post(`${A}/projects/:id/study/prompts/propose`, async () => { await delay(300); return HttpResponse.json(prompts) }),
  http.get(`${A}/projects/:id/study/prompts`, () => HttpResponse.json(prompts)),
  http.put(`${A}/projects/:id/study/prompts`, () => HttpResponse.json(prompts)),
  http.get(`${A}/projects/:id/study/prompts/instances`, () => HttpResponse.json(instances)),
  http.get(`${A}/projects/:id/study/config`, () => HttpResponse.json(studyConfig)),
  http.put(`${A}/projects/:id/study/config`, () => HttpResponse.json(studyConfig)),
  http.get(`${A}/estimates/study`, () => HttpResponse.json(estimatesStudy)),
  http.get(`${A}/estimates/analysis`, () => HttpResponse.json(estimatesAnalysis)),
  http.post(`${A}/projects/:id/run`, () => { running = true; return HttpResponse.json({ ...progress, estado: 'en_ejecucion' }, { status: 202 }) }),
  http.post(`${A}/projects/:id/run/resume`, () => { running = true; return HttpResponse.json({ ...progress, estado: 'en_ejecucion' }, { status: 202 }) }),
  http.post(`${A}/projects/:id/run/retry-step`, () => HttpResponse.json(progress, { status: 202 })),
  http.post(`${A}/projects/:id/run/cancel`, () => { running = false; return HttpResponse.json(progress) }),
  http.get(`${A}/projects/:id/progress`, () => HttpResponse.json(progress)),
  sse<SseEvents>(`${A}/projects/:id/events`, async ({ client }) => {
    client.send({ event: 'snapshot', data: progress })
    if (running) {
      for (const [i, paso] of STEPS.entries()) {
        await delay(600)
        client.send({ event: 'step', data: { paso, estado: 'en_curso' } })
        client.send({ event: 'counter', data: { paso, hechos: i + 1, total: STEPS.length } })
        await delay(400)
        client.send({ event: 'step', data: { paso, estado: 'hecho', duracion_s: 1, llamadas: 0, coste_eur: 0 } })
      }
      client.send({ event: 'done', data: { estado: 'completado' } })
      running = false
    }
  }),
  http.get(`${A}/projects/:id/ficha`, () => HttpResponse.json(ficha)),
  http.put(`${A}/projects/:id/ficha`, () => HttpResponse.json(ficha)),
  http.get(`${A}/projects/:id/market`, () => HttpResponse.json(market)),
  http.put(`${A}/projects/:id/market`, () => HttpResponse.json(market)),
  http.get(`${A}/projects/:id/findings`, () => HttpResponse.json(findings)),
  http.patch(`${A}/projects/:id/findings/:hid`, ({ params }) => HttpResponse.json((findings as { id: string }[]).find((h) => h.id === params.hid) ?? findings[0])),
  http.get(`${A}/projects/:id/plan`, () => HttpResponse.json(plan)),
  http.put(`${A}/projects/:id/plan`, () => HttpResponse.json(plan)),
  http.post(`${A}/projects/:id/plan/simulate`, () => HttpResponse.json({ score_actual: 38.5, score_simulado: 52.1, puesto_actual: 7, puesto_simulado: 3, etiqueta: 'Escenario hipotético, no una predicción', detalle: {} })),
  http.post(`${A}/projects/:id/checkpoints/:n/approve`, () => HttpResponse.json(project)),
  http.get(`${A}/projects/:id/invalidation`, () => HttpResponse.json({ pasos: ['plan', 'write', 'review', 'export'], estimacion: estimatesAnalysis })),
  http.post(`${A}/projects/:id/recompute`, () => HttpResponse.json(progress, { status: 202 })),
  http.get(`${A}/projects/:id/diagnosis`, ({ request }) => HttpResponse.json(new URL(request.url).searchParams.get('ambito') === 'asistida' ? diagnosisAsi : diagnosisEsp)),
  http.get(`${A}/projects/:id/tables/:tid`, ({ params }) => {
    const t = tables[`./fixtures/tables/${String(params.tid)}.json`]
    return t ? HttpResponse.json(t as object) : HttpResponse.json({ error: { code: 'no_existe', message: 'La tabla no existe.', detail: {} } }, { status: 404 })
  }),
  http.get(`${A}/projects/:id/executions`, () => HttpResponse.json(executions)),
  http.get(`${A}/projects/:id/executions/:eid`, () => HttpResponse.json(executionDetail)),
  http.get(`${A}/projects/:id/proposal`, () => HttpResponse.json(proposal)),
  http.post(`${A}/projects/:id/proposal/regenerate`, () => HttpResponse.json(progress, { status: 202 })),
  http.get(`${A}/projects/:id/exports/:fmt`, () => new HttpResponse('# Propuesta (fixture)', { headers: { 'Content-Type': 'text/markdown' } })),
  http.get(`${A}/projects/:id/quality`, () => HttpResponse.json(quality)),
  http.post(`${A}/projects/:id/quality/labels`, () => HttpResponse.json(quality)),
  http.patch(`${A}/projects/:id/quality/discrepancies/:eid/:marca`, () => HttpResponse.json(quality)),
  http.get(`${A}/projects/:id/traces`, () => HttpResponse.json(traces)),
]
