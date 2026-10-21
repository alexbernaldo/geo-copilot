# Producto: Preload

Regenerado en W0 a partir de la Parte A de `GUIA_WEB_GEO_COPILOT.md` (producto web, cualquier sector, un consultor, sin demo).

## Qué es
Estación de trabajo para consultores de GEO (Generative Engine Optimization) de una agencia como reload. Convierte el brief de una marca y un estudio de cómo la citan los asistentes de IA (ChatGPT, Gemini, Perplexity, Claude) en un diagnóstico de visibilidad trazable, hallazgos priorizados con evidencia, un plan de acción presupuestado y una propuesta lista para el cliente (o un dossier y un correo comercial para un prospecto).

Aplicación web local (React + FastAPI): un consultor, sin login, cada análisis es un proyecto guardado en disco. Cualquier sector. La web arranca vacía: no hay demo, botón de demo ni datos de ejemplo.

## Usuarios
- Consultor de la agencia, en su portátil. Sabe de marketing y SEO, no de programación. Usa la herramienta varias veces por semana con proyectos de sectores distintos. Necesita llegar de un brief a una propuesta en una tarde, defender cada cifra delante del cliente, controlar el gasto en APIs antes de gastarlo e intervenir en los momentos clave.
- Lector secundario: el comité del cliente (marketing + dirección), que solo ve el documento exportado.

## Modo
Operate: herramienta de trabajo con tablas y gráficos, no una página de marketing. Superficies de Read en la Propuesta. Escáner rápido, consistencia, densidad calma.

## Tono
Profesional, preciso, sobrio. Español de España; números con formato es-ES (`39,4 %`, `24.300 €`). Sin emojis, sin lenguaje de marketing, sin ilustraciones genéricas.

## Principios de diseño
1. Herramienta de trabajo, no página de marketing: densidad calma, jerarquía clara, sin decoración que no informe.
2. Cada cifra dice de dónde sale (tabla y n) y quién la produjo (cálculo, IA, consultor).
3. Espontánea y asistida nunca se mezclan, y cada una tiene una identidad visual constante en toda la web.
4. Un color para la marca del proyecto y uno para el líder, constantes en todos los gráficos. El resto, neutros.
5. Los puntos de control son el pulso del flujo: siempre se ve cuál toca y cuál está aprobado.
6. El coste se ve antes de gastarlo: ninguna acción con coste sin estimación y confirmación.
7. Claro y oscuro.
8. Sin emojis, sin lenguaje de marketing, sin ilustraciones genéricas.

## Regla de origen
La web nunca afirma que un texto lo escribió un modelo concreto si no fue así: «Redactado por IA · <modelo>» solo si el paso lo hizo un LLM real; «Generado automáticamente» si fue plantilla, reglas o degradación; «Calculado» para cifras; «Editado» si lo cambió el consultor.

## Restricciones
- Pantallas de 1280 px como objetivo; usable en 1024 px; nada se rompe en una tablet.
- Accesible: teclado, foco visible, contraste AA, gráficos con texto alternativo o tabla equivalente.
- Funciona sin red salvo la IA real: tipografías y recursos servidos en local.
- Contratos de datos del motor (`geo/schemas.py`) y de la API (`contracts/openapi.yaml`) no se cambian sin pasar por el líder.
