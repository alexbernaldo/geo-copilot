"""Carga y validación de los archivos CSV del kit."""

from pathlib import Path
import re
import pandas as pd

from geo.config import (
    BANCO_PROMPTS_CSV,
    CIUDADES_CONOCIDAS,
    EJECUCIONES_CSV,
    FUENTES_CATALOGO_CSV,
    INSTANCIACIONES_ESPONTANEAS,
    MARCAS_CSV,
    MUESTRA_EVALUADA_CSV,
)
from geo.schemas import (
    Ejecucion,
    Marca,
    Prompt,
    TipoFuente,
)


def _extract_city(prompt_text: str, ciudades: list[str] | None = None) -> str | None:
    """Extrae la ciudad mencionada en un prompt de instanciación 'ciudad'."""
    lista_ciudades = ciudades or CIUDADES_CONOCIDAS
    for ciudad in lista_ciudades:
        if re.search(rf"\b{re.escape(ciudad)}\b", prompt_text, flags=re.IGNORECASE):
            return ciudad
    return None


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


def load_marcas(path: Path = MARCAS_CSV) -> list[Marca]:
    """Carga las marcas del sector desde marcas.csv."""
    df = pd.read_csv(path, encoding="utf-8-sig")
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


def load_prompts(path: Path = BANCO_PROMPTS_CSV) -> list[Prompt]:
    """Carga el banco de prompts desde banco_prompts.csv."""
    df = pd.read_csv(path, encoding="utf-8-sig")
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


def load_fuentes(path: Path = FUENTES_CATALOGO_CSV) -> dict[str, tuple[TipoFuente, float]]:
    """Carga el catálogo de fuentes: dominio -> (TipoFuente, calidad)."""
    df = pd.read_csv(path, encoding="utf-8-sig")
    catalogo: dict[str, tuple[TipoFuente, float]] = {}
    for _, row in df.iterrows():
        dominio = str(row["Dominio"]).strip().lower()
        tipo: TipoFuente = str(row["Tipo_de_fuente"]).strip()  # type: ignore[assignment]
        calidad = float(row["Calidad_de_fuente_0_1"])
        catalogo[dominio] = (tipo, calidad)
    return catalogo


def load_ejecuciones(
    path: Path = EJECUCIONES_CSV,
    prompts_path: Path = BANCO_PROMPTS_CSV,
    ciudades: list[str] | None = None,
) -> pd.DataFrame:
    """Carga ejecuciones.csv, lo une con banco_prompts para añadir instanciación y normaliza campos."""
    df_ej = pd.read_csv(path, encoding="utf-8-sig")
    df_pr = pd.read_csv(prompts_path, encoding="utf-8-sig")[["Prompt_ID", "Instanciación"]]

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

    df["instanciacion"] = df["instanciacion"].astype(str).str.strip()
    df["espontanea"] = df["instanciacion"].isin(INSTANCIACIONES_ESPONTANEAS)
    df["ciudad"] = df.apply(
        lambda r: _extract_city(str(r["prompt_ejecutado"]), ciudades)
        if r["instanciacion"] == "ciudad"
        else None,
        axis=1,
    )
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


def as_ejecuciones(
    path: Path = EJECUCIONES_CSV,
    prompts_path: Path = BANCO_PROMPTS_CSV,
    ciudades: list[str] | None = None,
) -> list[Ejecucion]:
    """Devuelve las ejecuciones validadas como lista de objetos Pydantic Ejecucion."""
    df = load_ejecuciones(path=path, prompts_path=prompts_path, ciudades=ciudades)
    records = df.to_dict(orient="records")
    for rec in records:
        if pd.isna(rec.get("ciudad")):
            rec["ciudad"] = None
    return [Ejecucion(**rec) for rec in records]


def load_muestra(path: Path = MUESTRA_EVALUADA_CSV) -> pd.DataFrame:
    """Carga muestra_evaluada.csv renombrando sus columnas a los campos de Evaluacion."""
    df = pd.read_csv(path, encoding="utf-8-sig")
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


def dominios_desconocidos(
    ejecuciones_path: Path = EJECUCIONES_CSV,
    prompts_path: Path = BANCO_PROMPTS_CSV,
    fuentes_path: Path = FUENTES_CATALOGO_CSV,
) -> list[str]:
    """Devuelve la lista ordenada de dominios citados en ejecuciones que no están en el catálogo."""
    catalogo = load_fuentes(fuentes_path)
    df_ej = load_ejecuciones(path=ejecuciones_path, prompts_path=prompts_path)
    citados: set[str] = set()
    for lista_dom in df_ej["fuentes"]:
        citados.update(lista_dom)
    return sorted(citados - set(catalogo.keys()))
