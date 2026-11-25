"""
FIPP 2.0 — Phase 8 Stage B Non-Destructive Performance Benchmark.

Runs completely against isolated temporary storage (tempfile.TemporaryDirectory)
to benchmark cold/warm API latency, PBKDF2 authentication timing, 500-record
query/analytics scaling, upload validation, and process memory footprint.
"""
from __future__ import annotations

import copy
import ctypes
import io
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core import security
from app.core.config import PRIMARY_JSON_DATA_FILE
from app.main import app
from app.services import upload_service
from app.services.complaint_service import complaint_service
from app.api import routes_uploads


class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _get_rss_mb() -> float:
    try:
        counters = _PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return round(counters.WorkingSetSize / (1024 * 1024), 2)
    except Exception:
        pass
    return -1.0


def _time_calls(fn, iterations: int = 10) -> dict:
    samples = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples_sorted = sorted(samples)
    p95_idx = min(len(samples_sorted) - 1, max(0, int(len(samples_sorted) * 0.95) - 1))
    return {
        "iterations": iterations,
        "min_ms": round(min(samples), 2),
        "mean_ms": round(statistics.mean(samples), 2),
        "p95_ms": round(samples_sorted[p95_idx], 2),
        "max_ms": round(max(samples), 2),
    }


def _make_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=(15, 23, 42)).save(buf, format="PNG")
    return buf.getvalue()


def main() -> None:
    orig_data_file = complaint_service.data_file
    orig_upload_svc_dir = upload_service.UPLOAD_DIR
    orig_upload_route_dir = routes_uploads.UPLOAD_DIR
    orig_revoked_file = security._REVOKED_TOKENS_FILE
    orig_revoked_set = set(security._REVOKED_TOKENS)

    try:
        with tempfile.TemporaryDirectory(prefix="fipp_phase8_bench_") as tmp:
            tmp_path = Path(tmp)
            data_file = tmp_path / "complaints.json"
            base_records = json.loads(PRIMARY_JSON_DATA_FILE.read_text(encoding="utf-8"))
            data_file.write_text(json.dumps(base_records, indent=2), encoding="utf-8")

            upload_dir = tmp_path / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            revoked_file = tmp_path / "revoked_tokens.json"
            revoked_file.write_text("[]", encoding="utf-8")

            complaint_service.data_file = data_file
            upload_service.UPLOAD_DIR = upload_dir
            routes_uploads.UPLOAD_DIR = upload_dir
            security._REVOKED_TOKENS_FILE = revoked_file
            security._REVOKED_TOKENS = set()

            client = TestClient(app)

            rss_before_mb = _get_rss_mb()

            # Auth timing (includes OWASP 600k PBKDF2-HMAC-SHA256 verification)
            login_metrics = _time_calls(
                lambda: client.post("/api/auth/login", json={"username": "ADM-2026-001", "password": "Admin@001"}),
                iterations=5,
            )
            adm_token = client.post(
                "/api/auth/login",
                json={"username": "ADM-2026-001", "password": "Admin@001"},
            ).json()["access_token"]
            stu_token = client.post(
                "/api/auth/login",
                json={"username": "STU-2026-001", "password": "student123"},
            ).json()["access_token"]

            adm_hdr = {"Authorization": f"Bearer {adm_token}"}
            stu_hdr = {"Authorization": f"Bearer {stu_token}"}

            health_metrics = _time_calls(lambda: client.get("/api/health"), iterations=15)
            taxonomy_metrics = _time_calls(lambda: client.get("/api/taxonomy/hierarchy"), iterations=10)
            kpis_10_metrics = _time_calls(lambda: client.get("/api/admin/kpis", headers=adm_hdr), iterations=10)
            mcpi_metrics = _time_calls(
                lambda: client.get("/api/admin/intelligence/complaint/CMP-2026-001", headers=adm_hdr),
                iterations=10,
            )

            png_bytes = _make_png_bytes()
            upload_metrics = _time_calls(
                lambda: client.post(
                    "/api/uploads/photo",
                    headers=stu_hdr,
                    files={"file": ("bench.png", png_bytes, "image/png")},
                ),
                iterations=5,
            )

            # Expand isolated temp datastore to 500 records for pilot-scale query/analytics test
            expanded = []
            for idx in range(500):
                rec = copy.deepcopy(base_records[idx % len(base_records)])
                rec["complaint_id"] = f"CMP-2026-{idx + 1:03d}"
                expanded.append(rec)
            data_file.write_text(json.dumps(expanded), encoding="utf-8")

            kpis_500_metrics = _time_calls(lambda: client.get("/api/admin/kpis", headers=adm_hdr), iterations=10)
            search_500_metrics = _time_calls(
                lambda: client.get(
                    "/api/admin/complaints?limit=25&offset=0&priority=High&search=Block",
                    headers=adm_hdr,
                ),
                iterations=10,
            )
            analytics_500_metrics = _time_calls(
                lambda: client.get("/api/admin/reports/analytics?granularity=Weekly", headers=adm_hdr),
                iterations=5,
            )
            intel_500_metrics = _time_calls(
                lambda: client.get("/api/admin/intelligence/overview", headers=adm_hdr),
                iterations=5,
            )

            rss_after_mb = _get_rss_mb()

            report = {
                "baseline_record_count": len(base_records),
                "scaled_record_count": len(expanded),
                "process_rss_before_mb": rss_before_mb,
                "process_rss_after_mb": rss_after_mb,
                "benchmarks": {
                    "get_health": health_metrics,
                    "post_login_pbkdf2_600k": login_metrics,
                    "get_taxonomy_hierarchy": taxonomy_metrics,
                    "get_admin_kpis_10_records": kpis_10_metrics,
                    "get_complaint_mcpi_intelligence": mcpi_metrics,
                    "post_upload_photo_png": upload_metrics,
                    "get_admin_kpis_500_records": kpis_500_metrics,
                    "get_admin_complaints_search_filter_500_records": search_500_metrics,
                    "get_admin_reports_analytics_500_records": analytics_500_metrics,
                    "get_admin_intelligence_overview_500_records": intel_500_metrics,
                },
            }
            print(json.dumps(report, indent=2))
    finally:
        complaint_service.data_file = orig_data_file
        upload_service.UPLOAD_DIR = orig_upload_svc_dir
        routes_uploads.UPLOAD_DIR = orig_upload_route_dir
        security._REVOKED_TOKENS_FILE = orig_revoked_file
        security._REVOKED_TOKENS = orig_revoked_set


if __name__ == "__main__":
    main()
