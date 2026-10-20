"""CLI para ejecutar el pipeline completo de extremo a extremo (F12)."""

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from geo.config import BRIEF_MD
from geo.orchestrator import Run


def main() -> None:
    """Punto de entrada CLI del orquestador GEO Copilot."""
    parser = argparse.ArgumentParser(
        description="Ejecuta el pipeline completo de GEO Copilot de extremo a extremo."
    )
    parser.add_argument(
        "--brief",
        type=str,
        default=str(BRIEF_MD),
        help="Ruta al archivo de brief (.md, .docx, .txt)",
    )
    parser.add_argument(
        "--modo",
        choices=["cliente", "prospecto"],
        default="cliente",
        help="Modo de generación de propuesta (cliente | prospecto)",
    )
    parser.add_argument(
        "--marca",
        type=str,
        default=None,
        help="Nombre de la marca objetivo (obligatorio si --modo prospecto)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Identificador de la ejecución (p. ej. 'demo')",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "anthropic", "openai"],
        default=None,
        help="Proveedor LLM (por defecto usa LLM_PROVIDER de .env)",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Aprueba automáticamente todos los checkpoints humanos",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la re-ejecución de pasos aunque ya estén en done",
    )
    args = parser.parse_args()

    run = Run(
        run_id=args.run_id,
        modo=args.modo,  # type: ignore[arg-type]
        brief_path=args.brief,
        marca_prospecto=args.marca,
        provider=args.provider,
    )
    propuesta = run.run_all(
        auto_approve=args.auto_approve,
        force=args.force,
        stop_at_checkpoint=not args.auto_approve,
    )

    if propuesta is None:
        print(f"Run '{run.run_id}' pausado en checkpoint humano. Revisa {run.state_path}")
        return

    rev = propuesta.revision
    print(f"=== Pipeline completado con éxito · run_id={run.run_id} ===")
    print(f"Carpeta de salida    : {run.run_dir}")
    print(f"Marca                : {propuesta.marca} (modo={propuesta.modo})")
    print(
        f"Sello del revisor    : {rev.cifras_verificadas}/{rev.cifras_verificadas + rev.cifras_no_trazables} "
        f"cifras trazables · {len(rev.incidencias)} incidencias · Aprobado={rev.aprobado}"
    )


if __name__ == "__main__":
    main()
