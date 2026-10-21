# Contrato de componentes compartidos

Fija L en W0. Solo L cambia nombres y props (petición en `coord/peticiones/<agente>.md`). D implementa el estilo final sin tocar la API.
Importación: `import { Panel, KpiStrip } from '@/components'`.

| Componente | Props mínimas |
|---|---|
| `PageHeader` | `title`, `description?`, `actions?`, `checkpoint?: {n, approved}` |
| `Panel` | `title?`, `source?`, `actions?`, `children` |
| `KpiStrip` | `items: {label, value, unit?, note?, source?, highlight?}[]`, `scope?: "espontanea"\|"asistida"` |
| `ScopeToggle` | `value`, `onChange` |
| `Chip` | `tone: neutral\|good\|warn\|bad\|info\|spont\|assist\|accent`, `dot?` |
| `OriginTag` | `origen: calculado\|ia\|automatico\|editado`, `modelo?` |
| `SourceNote` | `tabla`, `n` (tooltip «Origen: T2 · n=60») |
| `EvidenceLink` | `ids: string[]`, `label?` (abre Datos del estudio filtrado) |
| `EmptyState` | `title`, `description`, `action?` |
| `PendingState` | `step` («Disponible cuando termine el paso X») |
| `ErrorState` | `error`, `onRetry?` |
| `CheckpointBar` | `n`, `approved`, `onApprove`, `summary` |
| `CostConfirm` | `estimate: Estimate`, `onConfirm`, `onCancel` |
| `DataTable` | envoltorio de TanStack Table: `columns`, `data`, `filters?`, `onRowClick?`, `editable?` |
| `Chart` | `option` (ECharts), `height?`, `ariaLabel`, `tableFallback?` |
| `useBrandColors` | `useBrandColors(marcaProyecto, lider)` → `(marca) => color` |
| `ProgressPanel` | `projectId` (usa `useProgress`) |
| `Markdown` | `source` |
| `Drawer`, `Dialog`, `Tabs`, `Tooltip`, `Button`, `Input`, `Select`, `Textarea`, `Checkbox`, `Slider` | API estándar tipo Radix |

Hooks comunes (D): `useProject`, `useProgress`, `useSettings` en `@/api/hooks`.

Reglas:
- Ninguna cifra se calcula en el cliente.
- Etiquetas de origen: `calculado` «Calculado», `ia` «Redactado por IA · <modelo>», `automatico` «Generado automáticamente», `editado` «Editado».
- Formato es-ES siempre desde `@/lib/format`.
