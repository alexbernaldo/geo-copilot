"""WC1 · Importación y validación de CSV del estudio."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from geo.study import csv_io
from geo.study.common import KIND_FILENAMES


def _copy_kit(kit_files: dict[str, Path], dest: Path, rename: bool = True) -> dict[str, Path]:
    dest.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for i, (kind, src) in enumerate(kit_files.items()):
        name = f"archivo_{i}.csv" if rename else src.name
        shutil.copyfile(src, dest / name)
        out[kind] = dest / name
    return out


def _edit(path: Path, fn) -> Path:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    df = fn(df)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def test_identify_por_columnas_no_por_nombre(kit_files: dict[str, Path], tmp_path: Path) -> None:
    copias = _copy_kit(kit_files, tmp_path)
    for kind, p in copias.items():
        assert csv_io.identify(p) == kind
    otro = tmp_path / "otro.csv"
    otro.write_text("a,b\n1,2\n", encoding="utf-8")
    assert csv_io.identify(otro) is None


def test_identify_tolera_bom_mayusculas_y_tildes(tmp_path: Path) -> None:
    p = tmp_path / "x.csv"
    p.write_text(
        "﻿EJECUCION_ID,PROMPT_ID,FAMILIA,INTENCION,PROMPT EJECUTADO,MOTOR,REPETICION,MARCAS A EVALUAR,RESPUESTA COMPLETA\n"
        "E1,P1,F,Descubrimiento,hola,chatgpt,1,A | B,texto\n",
        encoding="utf-8",
    )
    assert csv_io.identify(p) == "ejecuciones"
    df = csv_io.read_kind(p, "ejecuciones")
    assert list(df.columns)[:3] == ["Ejecucion_ID", "Sector", "Prompt_ID"]
    assert df.loc[0, "Repetición"] == "1"


def test_kit_validates_with_zero_errors(kit_files: dict[str, Path]) -> None:
    informes = csv_io.validate_set(kit_files)
    assert {r.tipo for r in informes} == set(kit_files)
    for r in informes:
        assert r.errores == [], (r.archivo, r.errores)
        assert r.filas > 0
    ej = next(r for r in informes if r.tipo == "ejecuciones")
    assert ej.filas == 624
    assert any("Fuentes citadas vacías" in a for a in ej.avisos)


def test_error_columna_obligatoria_ausente(kit_files: dict[str, Path], tmp_path: Path) -> None:
    copias = _copy_kit(kit_files, tmp_path)
    _edit(copias["ejecuciones"], lambda df: df.drop(columns=["Motor"]))
    rep = csv_io.validate("ejecuciones", copias["ejecuciones"])
    assert any("Motor" in e for e in rep.errores)
    # sin la columna deja de reconocerse como ejecuciones
    assert csv_io.identify(copias["ejecuciones"]) is None


def test_error_ejecucion_id_duplicado(kit_files: dict[str, Path], tmp_path: Path) -> None:
    copias = _copy_kit(kit_files, tmp_path)

    def dup(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[1, "Ejecucion_ID"] = df.loc[0, "Ejecucion_ID"]
        return df

    _edit(copias["ejecuciones"], dup)
    rep = csv_io.validate("ejecuciones", copias["ejecuciones"])
    assert any("duplicado" in e for e in rep.errores)
    assert rep.filas_con_error and rep.filas_con_error[0]["fila"] in (2, 3)


def test_error_motor_desconocido(kit_files: dict[str, Path], tmp_path: Path) -> None:
    copias = _copy_kit(kit_files, tmp_path)

    def mal(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[0, "Motor"] = "Bard"
        return df

    _edit(copias["ejecuciones"], mal)
    rep = csv_io.validate("ejecuciones", copias["ejecuciones"])
    assert any("Motor desconocido" in e and "Bard" in e for e in rep.errores)


def test_error_prompt_id_fuera_del_banco(kit_files: dict[str, Path], tmp_path: Path) -> None:
    copias = _copy_kit(kit_files, tmp_path)

    def mal(df: pd.DataFrame) -> pd.DataFrame:
        pid = df.loc[0, "Prompt_ID"]
        df.loc[df["Prompt_ID"] == pid, "Prompt_ID"] = "XXX-ZZ-99"
        return df

    _edit(copias["ejecuciones"], mal)
    informes = csv_io.validate_set(copias)
    ej = next(r for r in informes if r.tipo == "ejecuciones")
    assert any("Prompt_ID" in e and "XXX-ZZ-99" in e for e in ej.errores)


def test_error_marca_fuera_de_marcas(kit_files: dict[str, Path], tmp_path: Path) -> None:
    copias = _copy_kit(kit_files, tmp_path)

    def mal(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[0, "Marcas a evaluar"] = "Marca Inventada | Láser Nítida"
        return df

    _edit(copias["ejecuciones"], mal)
    informes = csv_io.validate_set(copias)
    ej = next(r for r in informes if r.tipo == "ejecuciones")
    assert any("Marca Inventada" in e for e in ej.errores)


def test_errores_en_marcas_banco_y_fuentes(kit_files: dict[str, Path], tmp_path: Path) -> None:
    copias = _copy_kit(kit_files, tmp_path)

    def marcas(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[1, "Nivel"] = "primario"
        return df

    def banco(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[1, "Prompt_ID"] = df.loc[0, "Prompt_ID"]
        df.loc[2, "Instanciación"] = "todas"
        return df

    def fuentes(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[0, "Tipo_de_fuente"] = "Blog"
        df.loc[1, "Calidad_de_fuente_0_1"] = "1,7"
        return df

    _edit(copias["marcas"], marcas)
    _edit(copias["banco_prompts"], banco)
    _edit(copias["fuentes_catalogo"], fuentes)
    assert any("Nivel" in e for e in csv_io.validate("marcas", copias["marcas"]).errores)
    errs = csv_io.validate("banco_prompts", copias["banco_prompts"]).errores
    assert any("duplicado" in e for e in errs) and any("Instanciación" in e for e in errs)
    errs = csv_io.validate("fuentes_catalogo", copias["fuentes_catalogo"]).errores
    assert any("Tipo de fuente" in e for e in errs) and any("Calidad" in e for e in errs)


def test_aviso_dominios_fuera_del_catalogo(kit_files: dict[str, Path], tmp_path: Path) -> None:
    copias = _copy_kit(kit_files, tmp_path)

    def sin(df: pd.DataFrame) -> pd.DataFrame:
        return df.iloc[:5].copy()

    _edit(copias["fuentes_catalogo"], sin)
    informes = csv_io.validate_set(copias)
    ej = next(r for r in informes if r.tipo == "ejecuciones")
    assert any("no están en el catálogo" in a for a in ej.avisos)
    assert ej.errores == []


def test_normalize_into_escribe_formato_canonico_y_resume(kit_files: dict[str, Path], tmp_path: Path) -> None:
    copias = _copy_kit(kit_files, tmp_path / "subidos")
    study = tmp_path / "study"
    resumen = csv_io.normalize_into(study, copias)
    for kind in kit_files:
        assert (study / KIND_FILENAMES[kind]).exists()
    assert resumen.ejecuciones == 624
    assert resumen.motores == ["ChatGPT", "Gemini", "Perplexity", "Claude"]
    assert resumen.repeticiones == 3
    assert resumen.prompts == 25
    assert resumen.marcas == 10
    assert resumen.espontaneas == 240 and resumen.asistidas == 384
    assert resumen.ciudades == ["Madrid", "Barcelona"]
    # UTF-8 con BOM
    assert (study / "ejecuciones.csv").read_bytes().startswith(b"\xef\xbb\xbf")


def test_normalize_into_es_legible_por_el_loader(kit_files: dict[str, Path], tmp_path: Path) -> None:
    from geo import loader

    copias = _copy_kit(kit_files, tmp_path / "subidos")
    study = tmp_path / "study"
    csv_io.normalize_into(study, copias)
    nuevo = loader.load_ejecuciones(path=study / "ejecuciones.csv", prompts_path=study / "banco_prompts.csv")
    kit = loader.load_ejecuciones(path=kit_files["ejecuciones"], prompts_path=kit_files["banco_prompts"])
    pd.testing.assert_frame_equal(nuevo.reset_index(drop=True), kit.reset_index(drop=True))
    assert [m.nombre for m in loader.load_marcas(study / "marcas.csv")] == [
        m.nombre for m in loader.load_marcas(kit_files["marcas"])
    ]
    assert loader.load_fuentes(study / "fuentes_catalogo.csv") == loader.load_fuentes(kit_files["fuentes_catalogo"])


def test_normalize_into_bloqueado_no_escribe_nada(kit_files: dict[str, Path], tmp_path: Path) -> None:
    copias = _copy_kit(kit_files, tmp_path / "subidos")

    def mal(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[0, "Motor"] = "Bard"
        return df

    _edit(copias["ejecuciones"], mal)
    study = tmp_path / "study"
    with pytest.raises(csv_io.StudyValidationError) as exc:
        csv_io.normalize_into(study, copias)
    assert exc.value.informes and not study.exists()


def test_normalize_unifica_motor_y_separadores(tmp_path: Path) -> None:
    ej = tmp_path / "e.csv"
    ej.write_text(
        "Ejecucion_ID,Prompt_ID,Familia,Intención,Prompt ejecutado,Motor,Repetición,Marcas a evaluar,Respuesta completa,Fuentes citadas\n"
        'E1,P1,F,Descubrimiento,hola,chatgpt,1,"A|B","texto","https://www.uno.es/x;dos.com"\n',
        encoding="utf-8",
    )
    pb = tmp_path / "b.csv"
    pb.write_text(
        "Prompt_ID,Familia,Intención,Prioridad,Uso,Instanciación,Prompt (plantilla)\n"
        "P1,F,Descubrimiento,P1,Publicable,generico,¿Hola qué tal?\n",
        encoding="utf-8",
    )
    mc = tmp_path / "m.csv"
    mc.write_text("Marca,Nivel,Rol,Dominio_propio,Alias\nA,foco,MARCA DEL BRIEF,www.a.com,\nB,contexto,x,b.com,Be|Bee\n", encoding="utf-8")
    study = tmp_path / "study"
    csv_io.normalize_into(study, {"ejecuciones": ej, "banco_prompts": pb, "marcas": mc})
    df = pd.read_csv(study / "ejecuciones.csv", encoding="utf-8-sig", dtype=str)
    assert df.loc[0, "Motor"] == "ChatGPT"
    assert df.loc[0, "Marcas a evaluar"] == "A | B"
    assert df.loc[0, "Fuentes citadas"] == "uno.es, dos.com"
    m = pd.read_csv(study / "marcas.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    assert m.loc[0, "Dominio_propio"] == "a.com" and m.loc[1, "Alias"] == "Be | Bee"
