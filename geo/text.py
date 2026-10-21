"""Normalización de texto y segmentación por marca."""

import re
import unicodedata

from geo.schemas import Marca

_CLOSING_PREFIXES: tuple[str, ...] = (
    "conviene contrastar",
    "en conjunto,",
    "en resumen",
    "consejo:",
    "si tuviera que senalar una",
    "tambien conviene",
    "no puedo garantizar",
)


def strip_accents(s: str) -> str:
    """Elimina tildes y marcas diacríticas usando descomposición NFKD."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


# Número con separadores que no forma parte de un identificador (EJ-0001, claude-4.5, v1.2, 2026-10-21, schema.org)
_NUM_TOKEN = re.compile(r"(?<![\w.,/])(?<!\w-)(\d+(?:[.,]\d+)+)(?![\w]|[.,]\d)(\s?€)?")
_PCT_PEGADO = re.compile(r"(?<=\d)%")


def _numero_es(m: re.Match[str]) -> str:
    tok, euro = m.group(1), m.group(2) or ""
    if "." in tok and "," in tok:
        if tok.rfind(",") < tok.rfind("."):  # 1,234.5 (inglés) -> 1.234,5
            tok = tok.replace(",", "\0").replace(".", ",").replace("\0", ".")
        return tok + euro
    partes = re.split(r"[.,]", tok)
    miles = len(partes[0]) <= 3 and not partes[0].startswith("0") and all(len(p) == 3 for p in partes[1:])
    if "." in tok:
        # 1.800 / 90.000 ya son miles en español; 27.97 o 0.3875 son decimales en inglés
        if not miles and len(partes) == 2:
            tok = tok.replace(".", ",")
    elif euro and miles:
        # 24,300 € es un importe en inglés; 4,7 o 0,479 sin € son decimales en español y se dejan
        tok = tok.replace(",", ".")
    return tok + euro


def formato_es(texto: str) -> str:
    """Pasa a formato es-ES las cifras escritas en formato inglés: `27.97` -> `27,97`, `24,300 €` -> `24.300 €`, `41.2%` -> `41,2 %`.

    Deja intactas las cifras que ya están en español (`1.800`, `38,8 %`) y los identificadores con números.
    """
    if not texto:
        return texto
    return _PCT_PEGADO.sub(" %", _NUM_TOKEN.sub(_numero_es, texto))


def normalize(s: str) -> str:
    """Normaliza un texto: minúsculas, sin tildes (NFKD), sin '**', sin citas '[1]' y espacios colapsados."""
    if not s:
        return ""
    cleaned = s.replace("**", " ")
    cleaned = re.sub(r"\[\d+\]", " ", cleaned)
    cleaned = strip_accents(cleaned).lower()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _prepare_search_views(text: str) -> tuple[str, str]:
    """Devuelve dos vistas alineadas carácter a carácter: (sin_tildes_con_mayus, normalizada_minus).

    Sustituye '**' y '[n]' por espacios de igual longitud para preservar posiciones y límites de palabra.
    """
    cleaned = re.sub(r"\*\*|\[\d+\]", lambda m: " " * len(m.group(0)), text)
    no_accents_case = strip_accents(cleaned)
    no_accents_lower = no_accents_case.lower()
    return no_accents_case, no_accents_lower


def find_brand_matches(text: str, marca: Marca) -> list[tuple[int, int, str]]:
    """Devuelve todas las coincidencias válidas (start, end, término) de una marca o sus alias.

    Ordena primero el nombre completo y después cada alias de más largo a más corto.
    Aplica las reglas anti-falsos-positivos del plan:
    - 'Nítida' solo cuenta si va en mayúscula en el original o precedida de 'Láser'.
    - 'Lasik' genérico no cuenta; solo cuenta el nombre o el alias completo 'Lasik Península'.
    - 'Cervantes' y 'Santa Eulalia' se buscan por palabra completa (se acepta y documenta el riesgo de calle).
    """
    if not text:
        return []

    no_accents_case, no_accents_lower = _prepare_search_views(text)

    # Primero el nombre completo, luego los alias ordenados de más largo a más corto
    candidates: list[str] = [marca.nombre] + sorted(marca.alias, key=len, reverse=True)
    seen_norms: set[str] = set()
    ordered_candidates: list[str] = []
    for cand in candidates:
        c_norm = normalize(cand)
        if c_norm and c_norm not in seen_norms:
            seen_norms.add(c_norm)
            ordered_candidates.append(c_norm)

    matches: list[tuple[int, int, str]] = []
    occupied_spans: list[tuple[int, int]] = []

    for cand_norm in ordered_candidates:
        words = cand_norm.split()
        pat_str = r"\b" + r"\s+".join(re.escape(w) for w in words) + r"\b"
        for m in re.finditer(pat_str, no_accents_lower):
            start, end = m.span()
            if any(not (end <= s or start >= e) for s, e in occupied_spans):
                continue

            if cand_norm == "nitida":
                orig_token = no_accents_case[start:end]
                prefix = no_accents_lower[max(0, start - 12) : start]
                is_capitalized = bool(orig_token and orig_token[0].isupper())
                has_laser_prefix = bool(re.search(r"\blaser\s+$", prefix))
                if not (is_capitalized or has_laser_prefix):
                    continue

            occupied_spans.append((start, end))
            matches.append((start, end, cand_norm))

    matches.sort(key=lambda item: item[0])
    return matches


def find_first_offset(text: str, marca: Marca) -> int | None:
    """Devuelve el offset del primer match válido de la marca en el texto, o None si no aparece."""
    matches = find_brand_matches(text, marca)
    if not matches:
        return None
    return matches[0][0]


def segmentos_por_marca(
    respuesta: str,
    marca: Marca,
    todas_las_marcas: list[Marca] | None = None,
) -> list[str]:
    """Extrae los segmentos de texto (bloques o secuencias de oraciones) donde se menciona a la marca.

    - Si la respuesta tiene varios bloques (líneas/viñetas), devuelve los bloques donde aparece la marca.
    - Si es un único bloque de prosa continua, agrupa la oración donde aparece la marca y las oraciones
      siguientes hasta que aparece otra marca del sector o una frase de cierre general.
    """
    if not respuesta or find_first_offset(respuesta, marca) is None:
        return []

    lines = [ln.strip() for ln in respuesta.splitlines() if ln.strip()]
    if len(lines) > 1:
        return [ln for ln in lines if find_first_offset(ln, marca) is not None]

    # Respuesta en un solo párrafo: segmentar por oraciones
    text = lines[0]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    other_brands = [m for m in (todas_las_marcas or []) if m.nombre != marca.nombre]

    segments: list[str] = []
    i = 0
    n = len(sentences)
    while i < n:
        sent = sentences[i]
        if find_first_offset(sent, marca) is not None:
            sent_norm = normalize(sent)
            is_closing = sent_norm.startswith(_CLOSING_PREFIXES)
            chunk = [sent]
            i += 1
            if not is_closing:
                while i < n:
                    next_sent = sentences[i]
                    next_norm = normalize(next_sent)
                    if next_norm.startswith(_CLOSING_PREFIXES):
                        break
                    if any(find_first_offset(next_sent, ob) is not None for ob in other_brands):
                        break
                    if find_first_offset(next_sent, marca) is not None:
                        break
                    chunk.append(next_sent)
                    i += 1
            segments.append(" ".join(chunk))
        else:
            i += 1

    return segments
