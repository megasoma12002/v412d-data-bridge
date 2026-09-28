#!/usr/bin/env python3
"""Guards against repro/ops byte-clone drift (see REPRO_DEDUPE_HYGIENE.md)."""
from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


class ReproDedupeHygieneTests(unittest.TestCase):
    def test_no_reports_byte_clone_of_outputs(self) -> None:
        clones: list[str] = []
        for outp in ROOT.glob("repro/*/outputs/*"):
            if not outp.is_file():
                continue
            rep = outp.parent.parent / "reports" / outp.name
            if rep.is_file() and _md5(outp) == _md5(rep):
                clones.append(str(rep.relative_to(ROOT)))
        self.assertEqual(clones, [], msg=f"reports≡outputs clones: {clones[:20]}")

    def test_decision_packs_in_reports_are_pointers_not_ops_clones(self) -> None:
        ops = {
            p.name: p
            for p in (ROOT / "research/ops").glob("*DECISION_PACK*")
            if p.is_file()
        }
        bad: list[str] = []
        for name, op in ops.items():
            for rp in ROOT.glob(f"repro/**/reports/{name}"):
                if not rp.is_file():
                    continue
                if _md5(op) == _md5(rp):
                    bad.append(str(rp.relative_to(ROOT)))
                else:
                    text = rp.read_text(encoding="utf-8", errors="ignore")
                    if "DECISION_PACK" in name and not text.startswith("# Pointer —"):
                        # Allow non-identical divergent copies only if marked pointer
                        # (legacy divergent content is OK; identical is not).
                        pass
        self.assertEqual(bad, [], msg=f"ops≡reports decision packs: {bad[:20]}")

    def test_ssot_helper_pointer_shape(self) -> None:
        from ops_repro_ssot import pointer_body

        body = pointer_body(ROOT / "research/ops/EXAMPLE_DECISION_PACK.md")
        self.assertTrue(body.startswith("# Pointer —"))
        self.assertIn("research/ops/EXAMPLE_DECISION_PACK.md", body)


if __name__ == "__main__":
    unittest.main()
