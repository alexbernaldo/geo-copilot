export interface Resaltado {
  marca: string
  inicio: number
  fin: number
}

export type Trozo = { texto: string; marca: string | null }

/** Parte la respuesta en trozos usando los desplazamientos que da la API. Los resaltados solapados se omiten. */
export function trocear(texto: string, resaltados: Resaltado[]): Trozo[] {
  const ordenados = [...resaltados].filter((r) => r.fin > r.inicio).sort((a, b) => a.inicio - b.inicio)
  const trozos: Trozo[] = []
  let cursor = 0
  for (const r of ordenados) {
    if (r.inicio < cursor || r.inicio >= texto.length) continue
    if (r.inicio > cursor) trozos.push({ texto: texto.slice(cursor, r.inicio), marca: null })
    const fin = Math.min(r.fin, texto.length)
    trozos.push({ texto: texto.slice(r.inicio, fin), marca: r.marca })
    cursor = fin
  }
  if (cursor < texto.length) trozos.push({ texto: texto.slice(cursor), marca: null })
  return trozos
}
