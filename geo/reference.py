"""Modo de referencia: detección fija del caso del kit (Clínica Alborada Visión)."""

import hashlib
import re
import unicodedata
from pathlib import Path

import pandas as pd

REFERENCE_DIR: Path = Path(__file__).resolve().parent / "reference_data"
REFERENCE_BRAND = "Clínica Alborada Visión"
REFERENCE_DOMAIN = "alboradavision.example"

REFERENCE_BRIEF_FILES: tuple[str, ...] = (
    "Brief_de_ejemplo_Clinica_Alborada.md",
    "Brief_de_ejemplo_Clinica_Alborada.docx",
)
REFERENCE_CSV_KINDS: tuple[str, ...] = (
    "ejecuciones",
    "marcas",
    "banco_prompts",
    "fuentes_catalogo",
    "muestra_evaluada",
)

# Generada por scripts/compute_reference_fingerprints.py. Un test la recalcula.
REFERENCE_FINGERPRINTS: dict[str, set[str]] = {
    "brief": {
        "00549a2c7b270b7e9afd2857611e926e090210d4af2b86139422b79f6e4b19ee",
        "c421646c5b426c1da385b2ee67d6cadad2017556d4b066cc2ff18d8c1378a565",
    },
    "ejecuciones": {
        "6fd8056cc029230e49bca53772891ef9b590a812aac06060cd6c745baa3ea346",
    },
    "marcas": {
        "c85867f9972aa8c8bd3af2c23faf7dc3423e25d380396e656282e754d4711e61",
    },
    "banco_prompts": {
        "6183d475d4fc6d774edcbff3bbfceb80d2f911b084978d2509e3d63c734e4515",
    },
    "fuentes_catalogo": {
        "bbf5598bb35a547fcb9bc47d5ae6b41ce7802f353464a2ef8f826f625ec63904",
    },
    "muestra_evaluada": {
        "9b9c52ecba3fd5262f84c208c015991e7dcbce772f4ce44d8b54d581c5b8c0ef",
    },
}

_MARKDOWN_CHARS = re.compile(r"[*#_`>|\-]")
_NON_ALNUM = re.compile(r"[\W_]+", re.UNICODE)


def normalize_for_fingerprint(text: str) -> str:
    """NFKC, minúsculas, sin tildes, sin marcas markdown, sin espacios ni puntuación."""
    t = unicodedata.normalize("NFKC", text).lower()
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    t = _MARKDOWN_CHARS.sub("", t)
    return _NON_ALNUM.sub("", t)


def fingerprint_text(text: str) -> str:
    return hashlib.sha256(normalize_for_fingerprint(text).encode("utf-8")).hexdigest()


def fingerprint_csv(path: Path) -> str:
    """sha256 de las filas (texto, columnas ordenadas, sin BOM ni finales de línea)."""
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    df = df[sorted(df.columns)]
    h = hashlib.sha256()
    h.update("\x1f".join(df.columns).encode("utf-8"))
    for row in df.itertuples(index=False):
        cells = (str(v).replace("\r\n", "\n").replace("\r", "\n") for v in row)
        h.update(b"\x1e" + "\x1f".join(cells).encode("utf-8"))
    return h.hexdigest()


def compute_reference_fingerprints() -> dict[str, set[str]]:
    """Calcula las huellas a partir de `reference_data/` (la usa el script y el test)."""
    from geo.intake import read_brief_text

    fps: dict[str, set[str]] = {"brief": set()}
    for name in REFERENCE_BRIEF_FILES:
        fps["brief"].add(fingerprint_text(read_brief_text(REFERENCE_DIR / name)))
    for kind in REFERENCE_CSV_KINDS:
        fps[kind] = {fingerprint_csv(REFERENCE_DIR / f"{kind}.csv")}
    return fps


def _kit_brands() -> tuple[set[str], set[str]]:
    df = pd.read_csv(REFERENCE_DIR / "marcas.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    names = {normalize_for_fingerprint(m) for m in df["Marca"]}
    domains = {normalize_for_fingerprint(d) for d in df["Dominio_propio"]}
    return names, domains


def detect_reference(
    *,
    brief_text: str | None,
    csv_paths: dict[str, Path] | None,
    prospect_brand: str | None,
    prospect_domain: str | None,
) -> tuple[bool, str]:
    """Devuelve (es_referencia, motivo). Motivo ∈ huella_brief, huella_datos, marca, dominio, ''."""
    brand_norm = normalize_for_fingerprint(REFERENCE_BRAND)
    domain_norm = normalize_for_fingerprint(REFERENCE_DOMAIN)

    brief_norm = normalize_for_fingerprint(brief_text) if brief_text else ""
    if brief_norm and hashlib.sha256(brief_norm.encode("utf-8")).hexdigest() in REFERENCE_FINGERPRINTS.get("brief", set()):
        return True, "huella_brief"

    ejec = (csv_paths or {}).get("ejecuciones")
    datos_kit = False
    if ejec is not None and Path(ejec).exists():
        datos_kit = fingerprint_csv(Path(ejec)) in REFERENCE_FINGERPRINTS.get("ejecuciones", set())
        if datos_kit:
            return True, "huella_datos"

    if brief_norm:
        if brand_norm in brief_norm:
            return True, "marca"
        if domain_norm in brief_norm:
            return True, "dominio"

    # Prospecto: marca o dominio del kit, con datos del kit o sin datos subidos.
    if not ejec or datos_kit:
        names, domains = _kit_brands()
        if prospect_brand and normalize_for_fingerprint(prospect_brand) in names:
            return True, "marca"
        if prospect_domain and normalize_for_fingerprint(prospect_domain) in domains:
            return True, "dominio"
    return False, ""
