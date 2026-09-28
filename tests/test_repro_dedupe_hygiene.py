#!/usr/bin/env python3
"""Guards against repro/ops byte-clone drift (see REPRO_DEDUPE_HYGIENE.md)."""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Sample of reports paths removed as outputs≡reports clones — outputs SSOT must remain.
_OUTPUTS_SSOT_SAMPLES = (
    "repro/priv-finhc-gate-v8-stagea/outputs/nav_V8_BULL_MA120_F05_EQ.csv",
    "repro/priv-finhc-cagr-mdd-gate-v7-stagea/outputs/nav_V7_REG_BULL_SIDE_F05_KDMAY.csv",
    "repro/cool-t50-inv-satellite-stagea/outputs/nav_COOL_INV_A25.csv",
    "repro/fuse-softsell-t50-inv-stagea/outputs/nav_SS_DWELL_A50.csv",
    "repro/mktdown-t50-inv-stagea/outputs/nav_MD_DD20_M8_A50.csv",
)

# Ban full-body dual-write of decision packs into repro/reports.
_REP_DECISION_PACK_WRITE = re.compile(
    r"""\(REP\s*/\s*[fF]?['\"][^'\"]*DECISION_PACK[^'\"]*['\"]\s*\)\s*\.write_text\s*\("""
)


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
        self.assertEqual(bad, [], msg=f"ops≡reports decision packs: {bad[:20]}")

    def test_pointer_targets_exist(self) -> None:
        missing: list[str] = []
        for rp in ROOT.glob("repro/**/reports/*DECISION_PACK*"):
            if not rp.is_file():
                continue
            text = rp.read_text(encoding="utf-8", errors="ignore")
            if not text.startswith("# Pointer —"):
                continue
            m = re.search(r"`([^`]+)`", text)
            if not m or not (ROOT / m.group(1)).is_file():
                missing.append(str(rp.relative_to(ROOT)))
        self.assertEqual(missing, [], msg=f"broken decision-pack pointers: {missing[:20]}")

    def test_outputs_ssot_still_present_after_reports_dedupe(self) -> None:
        missing = [p for p in _OUTPUTS_SSOT_SAMPLES if not (ROOT / p).is_file()]
        self.assertEqual(missing, [], msg=f"missing outputs SSOT: {missing}")

    def test_scripts_do_not_full_write_decision_pack_to_rep(self) -> None:
        offenders: list[str] = []
        for path in (ROOT / "scripts").glob("*.py"):
            if path.name in {"ops_repro_ssot.py", "check_project_coding_hygiene.py"}:
                continue
            text = path.read_text(encoding="utf-8")
            if _REP_DECISION_PACK_WRITE.search(text):
                offenders.append(path.name)
        self.assertEqual(
            offenders,
            [],
            msg="use write_ops_and_repro_pointer instead of REP DECISION_PACK write_text: "
            + ", ".join(offenders),
        )

    def test_ssot_helper_pointer_shape(self) -> None:
        from ops_repro_ssot import pointer_body, write_ops_and_repro_pointer
        import tempfile

        body = pointer_body(ROOT / "research/ops/EXAMPLE_DECISION_PACK.md")
        self.assertTrue(body.startswith("# Pointer —"))
        self.assertIn("research/ops/EXAMPLE_DECISION_PACK.md", body)

        with tempfile.TemporaryDirectory() as td:
            ops = Path(td) / "ops" / "FOO_DECISION_PACK.md"
            rep = Path(td) / "reports" / "FOO_DECISION_PACK.md"
            write_ops_and_repro_pointer(ops, rep, "# full\n")
            self.assertEqual(ops.read_text(encoding="utf-8"), "# full\n")
            self.assertTrue(rep.read_text(encoding="utf-8").startswith("# Pointer —"))
            self.assertNotEqual(ops.read_text(encoding="utf-8"), rep.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
