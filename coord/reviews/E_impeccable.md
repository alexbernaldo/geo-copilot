# Impeccable Critique & Audit · Pantallas de Análisis (E, ola 1)

- **Jerarquía:** 6 pantallas de análisis conectadas a MSW (Resumen, Ficha, Datos del estudio, Competencia, Diagnóstico, Hallazgos). Jerarquía clara con títulos semánticos y paneles modulados.
- **Formularios:** Ficha de marca implementada con validación Zod y useController para desacoplar componentes del kit. Indicación visible de campos faltantes y avisos de invalidación.
- **Tablas y gráficos:** Tablas equivalentes para cada gráfico T1-T12 en Diagnóstico; conmutador espontánea/asistida desacoplado; aria-label y descripciones textuales para accesibilidad.
- **Cifras y evidencias:** Cero cálculos en cliente (todas las métricas consumidas directamente de la API / MSW); EvidenceLink integrado en cada indicador con evidencia.
- **Colores:** Paleta de marcas gestionada vía `useBrandColors`, contrastes conformes WCAG AA.
