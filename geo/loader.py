"""Carga y validación de los CSV de un estudio (formato canónico del kit).

Todas las funciones reciben la carpeta del estudio (`study_dir`); no hay rutas por defecto.
"""

from pathlib import Path
import re
import pandas as pd

from geo.config import INSTANCIACIONES_ESPONTANEAS
from geo.schemas import (
    Ejecucion,
    Marca,
    Prompt,
    TipoFuente,
)

MARCAS_FILE = "marcas.csv"
BANCO_PROMPTS_FILE = "banco_prompts.csv"
EJECUCIONES_FILE = "ejecuciones.csv"
FUENTES_CATALOGO_FILE = "fuentes_catalogo.csv"
MUESTRA_EVALUADA_FILE = "muestra_evaluada.csv"

_MARCADOR_CIUDAD = "[CIUDAD]"


def _extract_city(prompt_text: str, ciudades: list[str] | None = None) -> str | None:
    """Busca en el prompt la primera ciudad de la lista (sin distinguir mayúsculas)."""
    for ciudad in ciudades or []:
        if re.search(rf"\b{re.escape(ciudad)}\b", prompt_text, flags=re.IGNORECASE):
            return ciudad
    return None


def detect_city_from_template(plantilla: str, prompt_ejecutado: str) -> str | None:
    """Obtiene la ciudad comparando el prompt instanciado con su plantilla (`[CIUDAD]`)."""
    if _MARCADOR_CIUDAD not in plantilla:
        return None
    partes = [re.escape(p) for p in plantilla.strip().split(_MARCADOR_CIUDAD)]
    patron = r"(.+?)".join(partes)
    patron = re.sub(r"(?:\\ )+", r"\\s+", patron)
    m = re.fullmatch(patron, prompt_ejecutado.strip(), flags=re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None


def _split_pipe(val: object) -> list[str]:
    """Divide una cadena por '|' eliminando espacios vacíos."""
    if pd.isna(val) or not str(val).strip():
        return []
    return [item.strip() for item in str(val).split("|") if item.strip()]


def _split_domains(val: object) -> list[str]:
    """Divide una cadena de dominios separados por coma, en minúsculas y sin espacios."""
    if pd.isna(val) or not str(val).strip():
        return []
    return [item.strip().lower() for item in str(val).split(",") if item.strip()]


def load_marcas(study_dir: Path) -> list[Marca]:
    """Carga las marcas del estudio desde marcas.csv."""
    p = Path(study_dir)
    file_path = p if p.suffix.lower() == ".csv" else p / MARCAS_FILE
    df = pd.read_csv(file_path, encoding="utf-8-sig")
    marcas: list[Marca] = []
    for _, row in df.iterrows():
        rol = str(row["Rol"]).strip()
        marcas.append(
            Marca(
                nombre=str(row["Marca"]).strip(),
                nivel=str(row["Nivel"]).strip(),  # type: ignore[arg-type]
                rol=rol,
                dominio=str(row["Dominio_propio"]).strip().lower(),
                alias=_split_pipe(row["Alias"]),
                es_marca_brief="MARCA DEL BRIEF" in rol.upper(),
            )
        )
    return marcas


def load_prompts(study_dir: Path) -> list[Prompt]:
    """Carga el banco de prompts desde banco_prompts.csv."""
    p = Path(study_dir)
    file_path = p if p.suffix.lower() == ".csv" else p / BANCO_PROMPTS_FILE
    df = pd.read_csv(file_path, encoding="utf-8-sig")
    prompts: list[Prompt] = []
    for _, row in df.iterrows():
        prompts.append(
            Prompt(
                prompt_id=str(row["Prompt_ID"]).strip(),
                familia=str(row["Familia"]).strip(),
                intencion=str(row["Intención"]).strip(),  # type: ignore[arg-type]
                prioridad=str(row["Prioridad"]).strip(),
                uso=str(row["Uso"]).strip(),
                instanciacion=str(row["Instanciación"]).strip(),  # type: ignore[arg-type]
                plantilla=str(row["Prompt (plantilla)"]).strip(),
            )
        )
    return prompts


def load_fuentes(study_dir: Path) -> dict[str, tuple[TipoFuente, float]]:
    """Carga el catálogo de fuentes: dominio -> (TipoFuente, calidad)."""
    p = Path(study_dir)
    file_path = p if p.suffix.lower() == ".csv" else p / FUENTES_CATALOGO_FILE
    df = pd.read_csv(file_path, encoding="utf-8-sig")
    catalogo: dict[str, tuple[TipoFuente, float]] = {}
    for _, row in df.iterrows():
        dominio = str(row["Dominio"]).strip().lower()
        tipo: TipoFuente = str(row["Tipo_de_fuente"]).strip()  # type: ignore[assignment]
        calidad = float(row["Calidad_de_fuente_0_1"])
        catalogo[dominio] = (tipo, calidad)
    return catalogo


def load_ejecuciones(
    study_dir: Path | None = None,
    ciudades: list[str] | None = None,
    *,
    path: Path | None = None,
    prompts_path: Path | None = None,
) -> pd.DataFrame:
    """Carga ejecuciones.csv, lo une con banco_prompts y normaliza campos.

    La ciudad de los prompts `ciudad` sale de `ciudades` (p. ej. las de la ficha) si se pasa;
    si no, de comparar el prompt ejecutado con la plantilla del banco.
    """
    if study_dir is None:
        if path is not None:
            study_dir = Path(path).parent
        else:
            raise ValueError("Se debe proporcionar study_dir o path.")
    study_dir = Path(study_dir)
    ej_file = Path(path) if path is not None else study_dir / EJECUCIONES_FILE
    pr_file = Path(prompts_path) if prompts_path is not None else study_dir / BANCO_PROMPTS_FILE
    df_ej = pd.read_csv(ej_file, encoding="utf-8-sig")
    df_pr_full = pd.read_csv(pr_file, encoding="utf-8-sig")
    df_pr = df_pr_full[["Prompt_ID", "Instanciación"]]
    plantillas = dict(zip(df_pr_full["Prompt_ID"], df_pr_full["Prompt (plantilla)"]))

    df = df_ej.merge(df_pr, on="Prompt_ID", how="left")
    if df["Instanciación"].isna().any():
        missing = df.loc[df["Instanciación"].isna(), "Prompt_ID"].unique().tolist()
        raise ValueError(f"Prompt_ID sin correspondencia en banco_prompts.csv: {missing}")

    df = df.rename(
        columns={
            "Ejecucion_ID": "ejecucion_id",
            "Sector": "sector",
            "Prompt_ID": "prompt_id",
            "Familia": "familia",
            "Intención": "intencion",
            "Instanciación": "instanciacion",
            "Prompt ejecutado": "prompt_ejecutado",
            "Motor": "motor",
            "Repetición": "repeticion",
            "Marcas a evaluar": "marcas_a_evaluar",
            "Respuesta completa": "respuesta",
            "Fuentes citadas": "fuentes",
            "Fecha/hora": "fecha",
        }
    )

    def _ciudad(r: pd.Series) -> str | None:
        if r["instanciacion"] != "ciudad":
            return None
        texto = str(r["prompt_ejecutado"])
        if ciudades:
            return _extract_city(texto, ciudades)
        return detect_city_from_template(str(plantillas.get(r["prompt_id"], "")), texto)

    df["instanciacion"] = df["instanciacion"].astype(str).str.strip()
    df["espontanea"] = df["instanciacion"].isin(INSTANCIACIONES_ESPONTANEAS)
    df["ciudad"] = df.apply(_ciudad, axis=1)
    df["fuentes"] = df["fuentes"].apply(_split_domains)
    df["marcas_a_evaluar"] = df["marcas_a_evaluar"].apply(_split_pipe)
    df["repeticion"] = df["repeticion"].astype(int)

    cols_order = [
        "ejecucion_id",
        "sector",
        "prompt_id",
        "familia",
        "intencion",
        "instanciacion",
        "prompt_ejecutado",
        "motor",
        "repeticion",
        "marcas_a_evaluar",
        "respuesta",
        "fuentes",
        "fecha",
        "ciudad",
        "espontanea",
    ]
    return df[cols_order]


def as_ejecuciones(study_dir: Path, ciudades: list[str] | None = None) -> list[Ejecucion]:
    """Devuelve las ejecuciones validadas como lista de objetos Pydantic Ejecucion."""
    df = load_ejecuciones(study_dir, ciudades=ciudades)
    records = df.to_dict(orient="records")
    for rec in records:
        if pd.isna(rec.get("ciudad")):
            rec["ciudad"] = None
    return [Ejecucion(**rec) for rec in records]


def load_muestra(study_dir: Path) -> pd.DataFrame:
    """Carga muestra_evaluada.csv renombrando sus columnas a los campos de Evaluacion."""
    p = Path(study_dir)
    file_path = p if p.suffix.lower() == ".csv" else p / MUESTRA_EVALUADA_FILE
    df = pd.read_csv(file_path, encoding="utf-8-sig")
    df = df.rename(
        columns={
            "Ejecucion_ID": "ejecucion_id",
            "Marca": "marca",
            "Aparece (1/0)": "aparece",
            "Posición": "posicion",
            "Peso posición": "peso_posicion",
            "Tipo de mención": "tipo_mencion",
            "Fuerza recomendación (-1 a 3)": "fuerza",
            "Sentimiento": "sentimiento",
            "Tipo de fuente": "tipo_fuente",
            "Fuente citada": "fuente_citada",
            "Respuesta completa": "respuesta",
            "Prompt_ID": "prompt_id",
            "Intención": "intencion",
            "Prompt ejecutado": "prompt_ejecutado",
            "Motor": "motor",
            "Repetición": "repeticion",
            "Fecha/hora": "fecha",
            "Notas": "notas",
            "Fuera de territorio": "fuera_de_territorio",
            "Sector": "sector",
        }
    )

    df["aparece"] = df["aparece"].astype(int)
    df["peso_posicion"] = df["peso_posicion"].astype(int)
    df["fuerza"] = df["fuerza"].astype(int)
    df["posicion"] = df["posicion"].apply(lambda v: None if pd.isna(v) else int(v))
    for col in ("tipo_mencion", "sentimiento", "tipo_fuente"):
        df[col] = df[col].apply(lambda v: None if pd.isna(v) else str(v).strip())

    return df


def dominios_desconocidos(study_dir: Path) -> list[str]:
    """Devuelve la lista ordenada de dominios citados en ejecuciones que no están en el catálogo."""
    catalogo = load_fuentes(study_dir)
    df_ej = load_ejecuciones(study_dir)
    citados: set[str] = set()
    for lista_dom in df_ej["fuentes"]:
        citados.update(lista_dom)
    return sorted(citados - set(catalogo.keys()))
