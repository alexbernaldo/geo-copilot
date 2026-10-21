import { Button, Chip, EmptyState, OriginTag, PageHeader } from '@/components'

/** Página /_kit (solo en desarrollo). D la completa en W1 con todos los componentes en todos sus estados. */
export default function KitPage() {
  return (
    <>
      <PageHeader title="Kit de componentes" description="Provisional de W0." />
      <Button>Botón</Button> <Chip tone="neutral">Chip</Chip> <OriginTag origen="calculado" />
      <EmptyState title="Estado vacío" description="Ejemplo." />
    </>
  )
}
