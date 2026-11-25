"""
FIPP 2.0 — Campus Block & Floor Reference Service.

Manages the neutral Campus -> Block -> Floor hierarchy using unverified external
reference defaults and administrator-controlled updates/verification overrides.
Enforces strict server-side block/floor validation without fabricating floors
for blocks whose floor counts are unknown.
"""
from __future__ import annotations

import copy
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import CAMPUS_BLOCKS_OVERRIDE_FILE, CAMPUS_BLOCKS_SEED_FILE

_LOCATION_LOCK = threading.RLock()


class LocationService:
    """Authoritative service for structured Campus Block & Floor reference metadata."""

    @staticmethod
    def _override_path() -> Path:
        env_override = os.environ.get("FIPP_CAMPUS_BLOCKS_FILE", "").strip()
        return Path(env_override) if env_override else CAMPUS_BLOCKS_OVERRIDE_FILE

    def load_blocks(self) -> List[Dict[str, Any]]:
        """Loads active block & floor reference list (admin override if present, else neutral seed)."""
        with _LOCATION_LOCK:
            override_path = self._override_path()
            source_path = override_path if override_path.is_file() else CAMPUS_BLOCKS_SEED_FILE
            if source_path.is_file():
                try:
                    data = json.loads(source_path.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        return copy.deepcopy(data)
                except Exception:
                    pass
            return []

    def _save_blocks(self, blocks: List[Dict[str, Any]]) -> None:
        override_path = self._override_path()
        override_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = override_path.with_suffix(".tmp")
        try:
            temp_path.write_text(json.dumps(blocks, indent=2), encoding="utf-8")
            os.replace(temp_path, override_path)
        except Exception as exc:
            raise RuntimeError("Failed to persist campus block reference safely.") from exc
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def get_block(self, block_identifier: str) -> Optional[Dict[str, Any]]:
        """Finds a block record by `block_id` or `display_name` (case-insensitive)."""
        if not block_identifier or not isinstance(block_identifier, str):
            return None
        needle = block_identifier.strip().casefold()
        for blk in self.load_blocks():
            if (
                str(blk.get("block_id", "")).strip().casefold() == needle
                or str(blk.get("display_name", "")).strip().casefold() == needle
            ):
                return blk
        return None

    def get_block_display_names(self) -> List[str]:
        """Returns ordered display names of configured campus blocks."""
        return [str(b["display_name"]) for b in self.load_blocks() if b.get("display_name")]

    def validate_block_floor_combination(
        self,
        building: str,
        block_id: Optional[str] = None,
        floor_id: Optional[str] = None,
        floor_label: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Validates server-side that:
        1. Selected block exists in active campus block reference.
        2. If block has configured floors (`len(floors) > 0`), floor selection is mandatory
           and MUST belong to that block (`floor_id` or `floor_label` exact match).
        3. If block has unknown/unconfigured floors (`len(floors) == 0`), fabricated floor values
           are rejected; `None` / empty / explicit unknown placeholder maps cleanly to `None`.
        """
        lookup_key = block_id or building
        block = self.get_block(lookup_key)
        if not block and building and block_id:
            block = self.get_block(building)
        if not block:
            raise ValueError(f"Selected campus block '{lookup_key}' is not a valid reference block.")

        if building and block.get("display_name") and building.strip().casefold() not in {
            str(block["display_name"]).casefold(),
            str(block["block_id"]).casefold(),
        }:
            raise ValueError("Block identifier and block display name do not match.")

        configured_floors = sorted(block.get("floors") or [], key=lambda f: int(f.get("sort_order", 0)))
        clean_fid = floor_id.strip() if isinstance(floor_id, str) and floor_id.strip() else None
        clean_flabel = floor_label.strip() if isinstance(floor_label, str) and floor_label.strip() else None

        if len(configured_floors) > 0:
            if not clean_fid and not clean_flabel:
                raise ValueError(
                    f"Floor selection is required for '{block['display_name']}'."
                )
            for fl in configured_floors:
                fid_match = clean_fid and str(fl.get("floor_id", "")).strip() == clean_fid
                lbl_match = clean_flabel and str(fl.get("floor_label", "")).strip().casefold() == clean_flabel.casefold()
                if fid_match or lbl_match:
                    if clean_fid and clean_flabel and not (fid_match and lbl_match):
                        raise ValueError(
                            f"Floor ID '{clean_fid}' does not match floor label '{clean_flabel}'."
                        )
                    return block, fl
            raise ValueError(
                f"Invalid floor selection for '{block['display_name']}'. Only configured floors for this block are allowed."
            )

        # Unknown / unverified floor count block: do NOT permit arbitrary fabricated floors
        if clean_fid or clean_flabel:
            raise ValueError(
                f"Block '{block['display_name']}' does not have configured floor records yet. "
                "Leave floor unspecified until an administrator verifies floors for this block."
            )
        return block, None

    def upsert_block(
        self,
        block_id: str,
        display_name: str,
        block_category: str,
        floor_labels: Optional[List[str]] = None,
        verification_status: str = "verified",
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Allows administrator to configure, verify, or update a block and its floor list."""
        clean_bid = block_id.strip().upper()
        if not clean_bid or not display_name.strip():
            raise ValueError("Both block_id and display_name are required.")

        allowed_statuses = {"unverified_external_reference", "verified", "conflict_flagged"}
        if verification_status not in allowed_statuses:
            raise ValueError(f"verification_status must be one of {sorted(allowed_statuses)}.")

        clean_labels = [lbl.strip() for lbl in (floor_labels or []) if isinstance(lbl, str) and lbl.strip()]
        floors_payload = [
            {
                "floor_id": f"{clean_bid}-F{idx}",
                "block_id": clean_bid,
                "floor_label": lbl,
                "sort_order": idx,
                "verification_status": verification_status,
            }
            for idx, lbl in enumerate(clean_labels)
        ]

        new_block = {
            "block_id": clean_bid,
            "display_name": display_name.strip(),
            "block_category": block_category.strip() or "Academic",
            "floor_count": len(floors_payload) if floors_payload else None,
            "floor_status": "verified" if (floors_payload and verification_status == "verified") else ("configured" if floors_payload else "unknown"),
            "verification_status": verification_status,
            "notes": (notes or "").strip() or None,
            "floors": floors_payload,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        with _LOCATION_LOCK:
            blocks = self.load_blocks()
            replaced = False
            for i, b in enumerate(blocks):
                if str(b.get("block_id", "")).upper() == clean_bid:
                    blocks[i] = new_block
                    replaced = True
                    break
            if not replaced:
                blocks.append(new_block)
            self._save_blocks(blocks)
            return new_block

    def import_blocks(self, blocks_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Replaces/updates block reference dataset from administrator-supplied validated JSON array."""
        if not isinstance(blocks_payload, list) or len(blocks_payload) == 0:
            raise ValueError("Import payload must be a non-empty list of block definitions.")

        validated: List[Dict[str, Any]] = []
        seen_ids = set()
        for item in blocks_payload:
            bid = str(item.get("block_id", "")).strip().upper()
            dname = str(item.get("display_name", "")).strip()
            if not bid or not dname or bid in seen_ids:
                raise ValueError(f"Invalid or duplicate block_id '{bid}' in import payload.")
            seen_ids.add(bid)

            floors_raw = item.get("floors") or []
            if not isinstance(floors_raw, list):
                raise ValueError(f"Invalid floors list on block '{bid}'.")

            vstatus = str(item.get("verification_status", "unverified_external_reference"))
            if vstatus not in {"unverified_external_reference", "verified", "conflict_flagged"}:
                raise ValueError(f"Invalid verification_status on block '{bid}'.")

            clean_floors = []
            for idx, fl in enumerate(floors_raw):
                lbl = str(fl.get("floor_label", "")).strip() if isinstance(fl, dict) else str(fl).strip()
                fid = str(fl.get("floor_id", f"{bid}-F{idx}")).strip() if isinstance(fl, dict) else f"{bid}-F{idx}"
                if not lbl:
                    continue
                clean_floors.append(
                    {
                        "floor_id": fid,
                        "block_id": bid,
                        "floor_label": lbl,
                        "sort_order": int(fl.get("sort_order", idx)) if isinstance(fl, dict) else idx,
                        "verification_status": str(fl.get("verification_status", vstatus)) if isinstance(fl, dict) else vstatus,
                    }
                )

            validated.append(
                {
                    "block_id": bid,
                    "display_name": dname,
                    "block_category": str(item.get("block_category", "Academic")).strip() or "Academic",
                    "floor_count": len(clean_floors) if clean_floors else None,
                    "floor_status": str(item.get("floor_status") or ("unknown" if not clean_floors else "configured")),
                    "verification_status": vstatus,
                    "notes": item.get("notes"),
                    "floors": clean_floors,
                }
            )

        with _LOCATION_LOCK:
            self._save_blocks(validated)
        return validated


location_service = LocationService()
