# Eventos en tiempo real (SSE)

`GET /api/projects/{id}/events` · `Content-Type: text/event-stream`.

Al conectar, el servidor envía primero un evento `snapshot` con el `Progress` completo (ver `openapi.yaml`). Después:

| Evento | `data` (JSON) | Frecuencia |
|---|---|---|
| `snapshot` | `Progress` | una vez al conectar |
| `step` | `{paso, estado, duracion_s?, llamadas?, coste_eur?, error?}` | en cada cambio de estado de un paso |
| `counter` | `{paso, hechos, total}` | máx. 4 por segundo |
| `cost` | `{llamadas, coste_eur, coste_real}` | máx. 1 por segundo |
| `checkpoint` | `{n, nombre}` | cuando se para esperando revisión |
| `done` | `{estado: completado\|error\|esperando_revision\|interrumpido, error?}` | al terminar el trabajo |
| `ping` | `{}` | cada 15 s |

`estado` de `step` ∈ `pendiente | en_curso | hecho | hecho_automatico | error | esperando_revision`.

Formato de cada mensaje:

```
event: step
data: {"paso":"judge","estado":"en_curso"}

```

## Cliente

- El frontend usa `EventSource` y, al reconectar, se apoya en `snapshot`.
- Si SSE falla, cae a sondeo de `GET /api/projects/{id}/progress` cada 2 s.
- El `JobRunner` escribe `run/progress.json` para sobrevivir a reinicios.
- Ninguna carga útil contiene campos de modo de referencia ni la clave de OpenRouter.
