# Herramientas de diseño y verificación (guía H1)

Instaladas a nivel de proyecto en W0 y versionadas en el repo:

| Herramienta | Dónde | Cómo se instaló |
|---|---|---|
| Emil Kowalski: `emil-design-eng`, `review-animations`, `improve-animations`, `animation-performance`, `break-ui` | `.claude/skills/` | `npx skills add emilkowalski/skills -a claude-code --copy` |
| Taste Skill: `design-taste-frontend` | `.claude/skills/` | `npx skills add https://github.com/Leonxlnx/taste-skill --skill design-taste-frontend -a claude-code --copy` |
| Impeccable (skills, agentes, motor y hooks) | `.claude/skills/impeccable`, `.claude/agents/` | `npx impeccable install -y --providers=claude --scope=project` |
| MCP `figma`, `lovable`, `playwright` | `.mcp.json` | `claude mcp add --scope project ...` (Playwright con `--isolated --headless`) |

Primera vez en cada máquina: aprobar los MCP del proyecto al abrir Claude Code y autenticarse en Figma y Lovable (OAuth en el navegador). Comprobar con `/mcp` y con `/skills`.

Los hooks de Impeccable (detector tras Edit/Write y pasada final) quedan en `.claude/settings.local.json`, que está ignorado por la configuración global de git: cada persona ejecuta `npx impeccable install -y --providers=claude --scope=project` para generarlos.

PRODUCT.md se escribió a mano a partir de la Parte A (equivalente a `/impeccable init`, que es interactivo). Si alguien ejecuta `/impeccable init`, debe conservar esos principios.
