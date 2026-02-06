from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from utils.compatibility import collect_system_report  # noqa: E402


def main() -> None:
    output = ROOT / "compat_report.json"
    if len(sys.argv) > 1:
        output = Path(sys.argv[1]).expanduser().resolve()
    report = collect_system_report()
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Compatibility report saved: {output}")


if __name__ == "__main__":
    main()
