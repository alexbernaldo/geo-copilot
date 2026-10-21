"""Calcula REFERENCE_FINGERPRINTS desde geo/reference_data/ e imprime la constante para pegarla en geo/reference.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from geo.reference import compute_reference_fingerprints  # noqa: E402


def main() -> None:
    fps = compute_reference_fingerprints()
    print("REFERENCE_FINGERPRINTS: dict[str, set[str]] = {")
    for key, values in fps.items():
        print(f'    "{key}": {{')
        for v in sorted(values):
            print(f'        "{v}",')
        print("    },")
    print("}")


if __name__ == "__main__":
    main()
