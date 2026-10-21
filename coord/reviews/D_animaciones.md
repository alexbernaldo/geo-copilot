# Animaciones · Emil Kowalski (D)

| Antes | Después | Por qué |
|---|---|---|
| Apertura instantánea sin transición | Transición con `cubic-bezier(0.32, 0.72, 0, 1)` a 250ms | Regla H2.1 para cajones laterales |
| Hover abrupto en botones | `transition: color, background 150ms ease` | Suavidad táctil sin lag perceptivo |
| Pulsación rígida | `:active { transform: scale(0.97); }` | Feedback táctil inmediato |
| Tooltip con pop-in | Fade + micro scale (0.95 -> 1.0) 125ms | Evitar parpadeos bruscos |
| Reducción de movimiento | `@media (prefers-reduced-motion) { ... }` | Accesibilidad obligatoria |
