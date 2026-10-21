# Producto: GEO Copilot

Supuestos inferidos de README.md y PLAN.md (no hubo entrevista de init).

## Qué es
Estación de trabajo de auditoría GEO (visibilidad de marcas en motores generativos). Un consultor de agencia carga un brief y el estudio de citación, revisa en cuatro puntos de control humanos y entrega una propuesta verificada.

## Usuarios
- Consultor GEO (reload.): opera el flujo completo, defiende cada cifra ante el cliente.
- Responsable de marketing de la clínica: lee diagnóstico, hallazgos y propuesta.
- Jurado del hackathon: evalúa rigor, trazabilidad y claridad en una demo de 5 minutos.

## Modo
Operate (con superficies de Read en Propuesta). Escáner rápido, consistencia, densidad calma.

## Tono
Profesional, preciso, sobrio. Español de España. Sin emoji, sin lenguaje de marketing.

## Principios de diseño
1. Cada cifra muestra su origen (tabla, n) y quién la produjo (código, IA, persona).
2. Espontánea y asistida nunca se mezclan: siempre rotuladas y con color propio.
3. Un acento (el color de la marca analizada) y neutros fríos; el color significa algo.
4. Los puntos de control humanos son el pulso del flujo, no un adorno.
5. Todo funciona sin red: tipografía y recursos en local.

## Restricciones
Streamlit 1.66, Python 3.11, sin cambiar contratos de datos (geo/schemas.py). Claro y oscuro.
