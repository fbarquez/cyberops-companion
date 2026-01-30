"""
Artifact Generator

Generates SAFE simulation artifacts for ransomware training scenarios.

IMPORTANT: This module creates benign artifacts that LOOK like ransomware
indicators but have NO malicious capability. All artifacts are clearly
marked as simulations.
"""

import sys
from pathlib import Path as PathLib

# Add project root to path for imports
PROJECT_ROOT = PathLib(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import uuid

from config import get_config


class ArtifactGenerator:
    """
    Generates safe ransomware simulation artifacts.

    All generated artifacts:
    - Are clearly marked as simulations
    - Have NO malicious capability
    - Can be easily cleaned up
    - Are tracked in a manifest for complete removal
    """

    SIMULATION_MARKER = "[IR_COMPANION_SIMULATION]"

    def __init__(self):
        """Initialize the artifact generator."""
        self.config = get_config()
        self.manifests: Dict[str, Dict[str, Any]] = {}

    def generate_artifacts(
        self,
        scenario: Any,  # SimulationScenario
        target_directory: Optional[Path] = None,
        simulation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate all artifacts for a scenario.

        Args:
            scenario: The simulation scenario
            target_directory: Where to create file artifacts
            simulation_id: Unique ID for this simulation run

        Returns:
            Dictionary of generated artifacts
        """
        sim_id = simulation_id or f"SIM-{uuid.uuid4().hex[:8].upper()}"

        artifacts = {
            "simulation_id": sim_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "files": [],
            "registry_keys": [],
            "log_entries": [],
        }

        config = scenario.artifacts_config

        # Generate ransom note
        if "ransom_note" in config:
            note_artifact = self._generate_ransom_note(
                config["ransom_note"],
                target_directory,
                sim_id,
            )
            artifacts["files"].append(note_artifact)

        # Generate "encrypted" files (just renamed, no actual encryption)
        if "encrypted_files" in config:
            enc_artifacts = self._generate_encrypted_file_indicators(
                config["encrypted_files"],
                target_directory,
                sim_id,
            )
            artifacts["files"].extend(enc_artifacts)

        # Generate registry key indicators (documented, not actually created)
        if "registry_key" in config:
            reg_artifact = self._generate_registry_indicator(
                config["registry_key"],
                sim_id,
            )
            artifacts["registry_keys"].append(reg_artifact)

        # Generate log entries
        if "process_artifacts" in config:
            log_artifacts = self._generate_log_entries(
                config["process_artifacts"],
                sim_id,
            )
            artifacts["log_entries"].extend(log_artifacts)

        # Store manifest for cleanup
        self.manifests[sim_id] = artifacts

        return artifacts

    def _generate_ransom_note(
        self,
        config: Dict[str, Any],
        target_dir: Optional[Path],
        sim_id: str,
    ) -> Dict[str, Any]:
        """Generate a safe ransom note file."""
        filename = config.get("filename", "README_RANSOMWARE.txt")
        variant = config.get("variant_name", "SimulatedRansomware")

        # Generate fake bitcoin address (clearly fake format)
        fake_btc = "1SimU1aTi0nFaKeBTCAddre55ForTra1n1ng"

        content = f"""{self.SIMULATION_MARKER}
================================================================================
                         THIS IS A TRAINING SIMULATION
                    NO ACTUAL ENCRYPTION HAS OCCURRED
================================================================================

--- SIMULATED RANSOM NOTE ---

Your files have been encrypted by {variant}!

To decrypt your files, send 0.5 BTC to:
{fake_btc}

After payment, contact: simulation@fake-ransomware.invalid

Your unique ID: {sim_id}

--- END SIMULATED RANSOM NOTE ---

================================================================================
                         THIS IS A TRAINING SIMULATION
          This file was created by IR Companion for educational purposes.
                         Created: {datetime.now(timezone.utc).isoformat()}
================================================================================
{self.SIMULATION_MARKER}
"""

        artifact_info = {
            "type": "ransom_note",
            "filename": filename,
            "variant": variant,
            "simulation_id": sim_id,
            "content_preview": content[:200] + "...",
        }

        # Write file if target directory specified
        if target_dir:
            target_dir = Path(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            file_path = target_dir / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            artifact_info["path"] = str(file_path)
            artifact_info["created"] = True
        else:
            artifact_info["created"] = False
            artifact_info["content"] = content

        return artifact_info

    def _generate_encrypted_file_indicators(
        self,
        config: Dict[str, Any],
        target_dir: Optional[Path],
        sim_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate files that appear to be encrypted.

        Note: These are NOT actually encrypted - they are plaintext files
        with a suspicious extension, containing clear simulation markers.
        """
        count = config.get("count", 5)
        extension = config.get("extension", ".encrypted_sim")

        artifacts = []

        sample_filenames = [
            "document",
            "spreadsheet",
            "presentation",
            "report",
            "data",
            "backup",
            "archive",
            "project",
            "notes",
            "config",
        ]

        for i in range(min(count, len(sample_filenames))):
            base_name = sample_filenames[i]
            filename = f"{base_name}{extension}"

            content = f"""{self.SIMULATION_MARKER}
This file simulates an encrypted file for training purposes.
Original filename: {base_name}.txt
Simulation ID: {sim_id}
Created: {datetime.now(timezone.utc).isoformat()}

NO ACTUAL ENCRYPTION - THIS IS A TRAINING ARTIFACT
{self.SIMULATION_MARKER}
"""

            artifact_info = {
                "type": "encrypted_file_indicator",
                "filename": filename,
                "original_name": f"{base_name}.txt",
                "extension": extension,
                "simulation_id": sim_id,
            }

            if target_dir:
                target_dir = Path(target_dir)
                target_dir.mkdir(parents=True, exist_ok=True)
                file_path = target_dir / filename

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                artifact_info["path"] = str(file_path)
                artifact_info["created"] = True
            else:
                artifact_info["created"] = False

            artifacts.append(artifact_info)

        return artifacts

    def _generate_registry_indicator(
        self,
        config: Dict[str, Any],
        sim_id: str,
    ) -> Dict[str, Any]:
        """
        Generate a registry key indicator.

        Note: This does NOT actually create a registry key - it documents
        what a real ransomware might create for educational purposes.
        """
        path = config.get("path", "HKCU\\Software\\SimulatedMalware")

        return {
            "type": "registry_indicator",
            "path": path,
            "simulation_id": sim_id,
            "description": "Simulated persistence registry key (NOT actually created)",
            "example_values": {
                "InstallPath": "C:\\Users\\victim\\AppData\\Local\\malware.exe",
                "RunKey": "SimulatedMalwareRun",
                "EncryptionKey": "BASE64_SIMULATED_KEY_DATA",
            },
            "note": "This registry key was NOT created - this is documentation only",
            "created": False,
        }

    def _generate_log_entries(
        self,
        config: Dict[str, Any],
        sim_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate simulated log entries.

        These represent what an analyst might find in logs during
        a real incident.
        """
        process_name = config.get("suspicious_process", "malware.exe")

        base_time = datetime.now(timezone.utc)

        entries = [
            {
                "type": "process_execution",
                "timestamp": base_time.isoformat(),
                "process": process_name,
                "parent_process": "explorer.exe",
                "command_line": f"C:\\Users\\victim\\Downloads\\{process_name}",
                "user": "DOMAIN\\victim_user",
                "simulation_id": sim_id,
            },
            {
                "type": "file_modification",
                "timestamp": base_time.isoformat(),
                "process": process_name,
                "action": "File renamed with ransomware extension",
                "path": "C:\\Users\\victim\\Documents\\*",
                "simulation_id": sim_id,
            },
            {
                "type": "network_connection",
                "timestamp": base_time.isoformat(),
                "process": process_name,
                "destination": "192.168.1.100:445",
                "protocol": "SMB",
                "note": "Possible lateral movement attempt",
                "simulation_id": sim_id,
            },
        ]

        return entries

    def cleanup(self, simulation_id: str) -> Dict[str, Any]:
        """
        Remove all artifacts for a simulation.

        Args:
            simulation_id: ID of the simulation to clean up

        Returns:
            Cleanup result summary
        """
        if simulation_id not in self.manifests:
            return {
                "success": False,
                "error": f"No manifest found for simulation {simulation_id}",
            }

        manifest = self.manifests[simulation_id]
        cleanup_result = {
            "simulation_id": simulation_id,
            "files_removed": 0,
            "files_failed": 0,
            "errors": [],
        }

        # Remove created files
        for file_info in manifest.get("files", []):
            if file_info.get("created") and "path" in file_info:
                try:
                    path = Path(file_info["path"])
                    if path.exists():
                        path.unlink()
                        cleanup_result["files_removed"] += 1
                except Exception as e:
                    cleanup_result["files_failed"] += 1
                    cleanup_result["errors"].append(str(e))

        cleanup_result["success"] = cleanup_result["files_failed"] == 0

        # Remove manifest
        del self.manifests[simulation_id]

        return cleanup_result

    def get_manifest(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get the artifact manifest for a simulation."""
        return self.manifests.get(simulation_id)

    def list_active_simulations(self) -> List[str]:
        """List all simulations with tracked artifacts."""
        return list(self.manifests.keys())
