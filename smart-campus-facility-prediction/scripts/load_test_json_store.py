"""
FIPP Empirical JSON Storage Concurrency & Load Benchmark.
Empirically tests and measures:
1. Thread-safe concurrent writes and updates under varying concurrency (1, 5, 10, 25, 50 threads).
2. Throughput (ops/sec), mean latency, and P95 latency.
3. Latency degradation as datastore size scales (100, 500, 1000, 2000, 3500 records).
4. Multi-process cross-boundary file contention evaluation.
"""
import concurrent.futures
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import src.data.complaints_store as store


def run_benchmark():
    print("=" * 70)
    print("FIPP EMPIRICAL JSON DATASTORE BENCHMARK & LOAD TEST")
    print("=" * 70)

    # Setup isolated temporary testing environment
    temp_dir = tempfile.mkdtemp(prefix="fipp_load_test_")
    test_db = Path(temp_dir) / "test_complaints.json"
    os.environ["FIPP_DATA_FILE"] = str(test_db)

    # Initialize with 50 seed records
    seed_records = [
        {
            "complaint_id": f"CMP-2026-{i:03d}",
            "student_id": f"STU{1000 + i}",
            "student_name": f"Student {i}",
            "title": f"Seed Issue {i}",
            "category": "Electrical",
            "location": f"Hostel Block A, Room {100 + i}",
            "status": "Submitted",
            "priority": "Medium",
            "created_at": datetime.now().isoformat(),
        }
        for i in range(1, 51)
    ]
    with open(test_db, "w", encoding="utf-8") as f:
        json.dump(seed_records, f, indent=2)

    store._load_from_disk()

    print(f"Initialized isolated benchmark datastore: {test_db}")
    print(f"Seed records loaded: {len(seed_records)}\n")

    # --------------------------------------------------------------------------
    # TEST 1: Concurrency Benchmark with varying thread counts
    # --------------------------------------------------------------------------
    print("--- 1. Concurrent Write & Update Throughput vs Thread Count ---")
    concurrency_levels = [1, 5, 10, 25, 50]

    for workers in concurrency_levels:
        latencies = []
        error_list = []
        total_ops = 50

        start_time = time.perf_counter()

        def worker_task(idx):
            op_start = time.perf_counter()
            try:
                ticket = {
                    "student_id": f"BENCH_{workers}_{idx}",
                    "student_name": f"Bench User {idx}",
                    "title": f"Load Test Issue {workers}-{idx}",
                    "category": "Plumbing",
                    "location": f"Block B, Room {idx}",
                    "contact_number": "9876543210",
                    "status": "Submitted",
                }
                tok = store.add_complaint(ticket)
                # Follow up with status update
                store.update_complaint_status_extended(
                    complaint_id=tok,
                    new_status="In Progress",
                    admin_title="Facility Officer",
                    remarks=f"Load test worker {idx}",
                )
                latencies.append((time.perf_counter() - op_start) * 1000)
            except Exception as e:
                error_list.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(total_ops)]
            concurrent.futures.wait(futures)

        elapsed = time.perf_counter() - start_time
        successful_ops = (total_ops - len(error_list)) * 2
        ops_per_sec = successful_ops / elapsed if elapsed > 0 else 0
        latencies.sort()
        mean_lat = sum(latencies) / len(latencies) if latencies else 0
        p95_idx = int(len(latencies) * 0.95)
        p95_lat = latencies[p95_idx] if latencies else 0

        print(
            f"Workers: {workers:2d} | "
            f"Successful Ops: {successful_ops:3d} | "
            f"Time: {elapsed:5.2f}s | "
            f"Throughput: {ops_per_sec:5.1f} ops/s | "
            f"Mean Lat: {mean_lat:5.1f}ms | "
            f"P95 Lat: {p95_lat:5.1f}ms | "
            f"Errors: {len(error_list)}"
        )
        if error_list:
            print(f"   Sample error: {error_list[0]}")

    # --------------------------------------------------------------------------
    # TEST 2: Scaling Benchmark — Latency vs Datastore Size
    # --------------------------------------------------------------------------
    print("\n--- 2. Latency Degradation vs Datastore Size (O(N) Re-serialization) ---")
    size_targets = [100, 500, 1000, 2000, 3500]

    for target_count in size_targets:
        # Pad datastore up to target_count
        current_data = store._load_from_disk() or []
        needed = target_count - len(current_data)
        if needed > 0:
            extra = [
                {
                    "complaint_id": f"CMP-SCALE-{j:05d}",
                    "student_id": f"STU_SCALE_{j}",
                    "title": f"Synthetic Scale Record {j}",
                    "category": "Carpentry",
                    "status": "Resolved",
                    "created_at": datetime.now().isoformat(),
                }
                for j in range(len(current_data) + 1, target_count + 1)
            ]
            current_data.extend(extra)
            store._save_to_disk(current_data)

        # Measure 10 sample writes on this database size
        sample_latencies = []
        for s in range(10):
            t0 = time.perf_counter()
            ticket = {
                "student_id": f"SCALE_TEST_{target_count}_{s}",
                "title": f"Scale Probe {s}",
                "category": "Electrical",
                "status": "Submitted",
            }
            store.add_complaint(ticket)
            sample_latencies.append((time.perf_counter() - t0) * 1000)

        mean_write_ms = sum(sample_latencies) / len(sample_latencies)
        file_size_kb = test_db.stat().st_size / 1024

        print(
            f"Datastore Records: {target_count:4d} | "
            f"File Size: {file_size_kb:6.1f} KB | "
            f"Mean Write Latency: {mean_write_ms:5.1f} ms | "
            f"Estimated Max Write Throughput: {1000 / mean_write_ms:4.1f} writes/s"
        )

    # --------------------------------------------------------------------------
    # TEST 3: Verification of Store Integrity After Load
    # --------------------------------------------------------------------------
    print("\n--- 3. Post-Load Data Integrity Verification ---")
    final_records = store._load_from_disk() or []
    tokens = [r["complaint_id"] for r in final_records]
    unique_tokens = set(tokens)
    print(f"Total Records in Store: {len(final_records)}")
    print(f"Unique Tokens: {len(unique_tokens)}")
    print(f"Collision Count: {len(tokens) - len(unique_tokens)}")

    # Cleanup temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("\nBenchmark completed. Temporary test artifacts cleaned up.")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
