"""BSI IT-Grundschutz automatic update service."""
import logging
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from uuid import uuid4

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.models.bsi_grundschutz import BSIBaustein, BSIAnforderung, BSIKategorie, BSIAnforderungTyp, BSISchutzbedarf
from src.core.redis import get_redis

logger = logging.getLogger(__name__)

# BSI GitHub sources
BSI_GITHUB_SOURCES = [
    {
        "name": "BSI-Bund OSCAL Catalog",
        "url": "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/main/Quellkataloge/Methodik-Grundschutz%2B%2B/BSI-Methodik-Grundschutz%2B%2B-catalog.json",
        "format": "oscal",
    },
    {
        "name": "BSI IT-Grundschutz Kompendium",
        "url": "https://raw.githubusercontent.com/BSI-Bund/IT-Grundschutz-Kompendium/main/data/kompendium.json",
        "format": "kompendium",
    },
]

# Fallback local path
LOCAL_DATA_PATH = "/app/src/db/data/bsi_grundschutz_2023.json"

# Redis keys
REDIS_KEY_VERSION = "bsi:catalog:version"
REDIS_KEY_LAST_CHECK = "bsi:catalog:last_check"
REDIS_KEY_LAST_UPDATE = "bsi:catalog:last_update"


class BSIUpdateService:
    """Service for automatic BSI catalog updates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_for_updates(self) -> Dict[str, Any]:
        """Check if there are updates available from BSI sources.

        Returns:
            Dict with update status and info
        """
        redis = await get_redis()

        result = {
            "has_updates": False,
            "current_version": None,
            "new_version": None,
            "source": None,
            "checked_at": datetime.utcnow().isoformat(),
        }

        # Get current version hash
        current_hash = await redis.get(REDIS_KEY_VERSION)
        result["current_version"] = current_hash

        # Try each source
        for source in BSI_GITHUB_SOURCES:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(source["url"])

                    if response.status_code == 200:
                        content = response.text
                        new_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

                        if current_hash != new_hash:
                            result["has_updates"] = True
                            result["new_version"] = new_hash
                            result["source"] = source["name"]
                            result["source_url"] = source["url"]
                            result["format"] = source["format"]
                            result["content"] = content

                            logger.info(f"BSI update available from {source['name']}: {current_hash} -> {new_hash}")
                            break
                        else:
                            logger.debug(f"BSI catalog up to date (hash: {current_hash})")

            except Exception as e:
                logger.warning(f"Failed to check {source['name']}: {e}")
                continue

        # Update last check timestamp
        await redis.set(REDIS_KEY_LAST_CHECK, datetime.utcnow().isoformat())

        return result

    async def apply_update(self, update_info: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a BSI catalog update to the database.

        Args:
            update_info: Update info from check_for_updates()

        Returns:
            Dict with update results
        """
        if not update_info.get("has_updates"):
            return {"success": False, "message": "No updates to apply"}

        redis = await get_redis()

        try:
            content = update_info.get("content")
            format_type = update_info.get("format")

            if not content:
                return {"success": False, "message": "No content to process"}

            data = json.loads(content)

            # Parse based on format
            if format_type == "oscal":
                bausteine, anforderungen = self._parse_oscal_format(data)
            elif format_type == "kompendium":
                bausteine, anforderungen = self._parse_kompendium_format(data)
            else:
                # Try to detect format
                bausteine, anforderungen = self._parse_auto_detect(data)

            if not bausteine:
                return {"success": False, "message": "No Bausteine found in update"}

            # Apply to database
            stats = await self._sync_to_database(bausteine, anforderungen)

            # Update version in Redis
            await redis.set(REDIS_KEY_VERSION, update_info["new_version"])
            await redis.set(REDIS_KEY_LAST_UPDATE, datetime.utcnow().isoformat())

            logger.info(f"BSI catalog updated: {stats}")

            return {
                "success": True,
                "message": "Update applied successfully",
                "stats": stats,
                "new_version": update_info["new_version"],
                "source": update_info["source"],
            }

        except Exception as e:
            logger.error(f"Failed to apply BSI update: {e}")
            return {"success": False, "message": str(e)}

    async def auto_update(self) -> Dict[str, Any]:
        """Check for updates and apply them automatically.

        This is the main method called by the Celery task.

        Returns:
            Dict with full update results
        """
        logger.info("Starting BSI auto-update check...")

        # Check for updates
        update_info = await self.check_for_updates()

        if not update_info["has_updates"]:
            return {
                "action": "check",
                "result": "up_to_date",
                "checked_at": update_info["checked_at"],
            }

        # Apply updates
        apply_result = await self.apply_update(update_info)

        return {
            "action": "update",
            "result": "success" if apply_result["success"] else "failed",
            "details": apply_result,
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get current BSI catalog status.

        Returns:
            Dict with catalog status info
        """
        redis = await get_redis()

        # Get counts from database
        baustein_count = await self.db.scalar(select(func.count()).select_from(BSIBaustein))
        anforderung_count = await self.db.scalar(select(func.count()).select_from(BSIAnforderung))

        return {
            "version": await redis.get(REDIS_KEY_VERSION),
            "last_check": await redis.get(REDIS_KEY_LAST_CHECK),
            "last_update": await redis.get(REDIS_KEY_LAST_UPDATE),
            "bausteine_count": baustein_count or 0,
            "anforderungen_count": anforderung_count or 0,
            "sources": [s["name"] for s in BSI_GITHUB_SOURCES],
        }

    def _parse_oscal_format(self, data: Dict) -> Tuple[list, list]:
        """Parse OSCAL format from BSI GitHub."""
        bausteine = []
        anforderungen = []

        catalog = data.get("catalog", data)
        groups = catalog.get("groups", [])

        for group in groups:
            kategorie = self._detect_kategorie(group.get("id", ""), group.get("title", ""))

            for control in group.get("controls", []):
                baustein_id = control.get("id", "")
                baustein = {
                    "baustein_id": baustein_id,
                    "kategorie": kategorie,
                    "titel": control.get("title", ""),
                    "beschreibung": self._extract_prose(control.get("parts", [])),
                    "version": "2023",
                }
                bausteine.append(baustein)

                # Extract requirements
                for part in control.get("parts", []):
                    if part.get("name") == "requirement":
                        anf = {
                            "baustein_id": baustein_id,
                            "anforderung_id": part.get("id", ""),
                            "titel": part.get("title", ""),
                            "beschreibung": part.get("prose", ""),
                            "typ": self._detect_typ(part.get("props", [])),
                        }
                        anforderungen.append(anf)

        return bausteine, anforderungen

    def _parse_kompendium_format(self, data: Dict) -> Tuple[list, list]:
        """Parse Kompendium format."""
        bausteine = []
        anforderungen = []

        for item in data.get("bausteine", data.get("items", [])):
            baustein = {
                "baustein_id": item.get("id", item.get("baustein_id", "")),
                "kategorie": item.get("kategorie", ""),
                "titel": item.get("titel", item.get("title", "")),
                "beschreibung": item.get("beschreibung", item.get("description", "")),
                "version": item.get("version", "2023"),
            }
            bausteine.append(baustein)

            for anf in item.get("anforderungen", []):
                anforderung = {
                    "baustein_id": baustein["baustein_id"],
                    "anforderung_id": anf.get("id", anf.get("anforderung_id", "")),
                    "titel": anf.get("titel", anf.get("title", "")),
                    "beschreibung": anf.get("beschreibung", anf.get("description", "")),
                    "typ": anf.get("typ", anf.get("type", "SOLLTE")),
                }
                anforderungen.append(anforderung)

        return bausteine, anforderungen

    def _parse_auto_detect(self, data: Dict) -> Tuple[list, list]:
        """Auto-detect format and parse."""
        if "catalog" in data:
            return self._parse_oscal_format(data)
        elif "bausteine" in data or "items" in data:
            return self._parse_kompendium_format(data)
        else:
            logger.warning("Unknown BSI data format, attempting generic parse")
            return self._parse_kompendium_format(data)

    async def _sync_to_database(self, bausteine: list, anforderungen: list) -> Dict[str, int]:
        """Sync parsed data to database.

        Uses upsert logic - updates existing, inserts new.
        """
        stats = {
            "bausteine_added": 0,
            "bausteine_updated": 0,
            "anforderungen_added": 0,
            "anforderungen_updated": 0,
        }

        # Process Bausteine
        for b_data in bausteine:
            baustein_id = b_data.get("baustein_id")
            if not baustein_id:
                continue

            # Check if exists
            result = await self.db.execute(
                select(BSIBaustein).where(BSIBaustein.baustein_id == baustein_id)
            )
            existing = result.scalar_one_or_none()

            kategorie = self._map_kategorie(b_data.get("kategorie", ""))

            if existing:
                # Update
                existing.titel = b_data.get("titel", existing.titel)
                existing.beschreibung = b_data.get("beschreibung", existing.beschreibung)
                existing.version = b_data.get("version", existing.version)
                stats["bausteine_updated"] += 1
            else:
                # Insert
                baustein = BSIBaustein(
                    id=str(uuid4()),
                    baustein_id=baustein_id,
                    kategorie=kategorie,
                    titel=b_data.get("titel", ""),
                    beschreibung=b_data.get("beschreibung"),
                    version=b_data.get("version", "2023"),
                )
                self.db.add(baustein)
                stats["bausteine_added"] += 1

        await self.db.flush()

        # Build baustein lookup
        result = await self.db.execute(select(BSIBaustein))
        baustein_lookup = {b.baustein_id: b.id for b in result.scalars().all()}

        # Process Anforderungen
        for a_data in anforderungen:
            anf_id = a_data.get("anforderung_id")
            baustein_id = a_data.get("baustein_id")

            if not anf_id or baustein_id not in baustein_lookup:
                continue

            result = await self.db.execute(
                select(BSIAnforderung).where(BSIAnforderung.anforderung_id == anf_id)
            )
            existing = result.scalar_one_or_none()

            typ = self._map_typ(a_data.get("typ", "SOLLTE"))
            schutzbedarf = self._determine_schutzbedarf(typ)

            if existing:
                existing.titel = a_data.get("titel", existing.titel)
                existing.beschreibung = a_data.get("beschreibung", existing.beschreibung)
                existing.typ = typ
                existing.schutzbedarf = schutzbedarf
                stats["anforderungen_updated"] += 1
            else:
                anforderung = BSIAnforderung(
                    id=str(uuid4()),
                    baustein_fk=baustein_lookup[baustein_id],
                    anforderung_id=anf_id,
                    titel=a_data.get("titel", ""),
                    beschreibung=a_data.get("beschreibung"),
                    typ=typ,
                    schutzbedarf=schutzbedarf,
                )
                self.db.add(anforderung)
                stats["anforderungen_added"] += 1

        await self.db.commit()

        return stats

    def _detect_kategorie(self, id_str: str, title: str) -> str:
        """Detect BSI category from ID or title."""
        id_upper = id_str.upper()
        for kat in ["ISMS", "ORP", "CON", "OPS", "DER", "APP", "SYS", "NET", "INF", "IND"]:
            if kat in id_upper:
                return kat
        return "OPS"  # Default

    def _map_kategorie(self, kat_str: str) -> BSIKategorie:
        """Map string to BSIKategorie enum."""
        try:
            return BSIKategorie(kat_str.upper())
        except ValueError:
            return BSIKategorie.OPS

    def _detect_typ(self, props: list) -> str:
        """Detect requirement type from OSCAL props."""
        for prop in props:
            if prop.get("name") == "label":
                value = prop.get("value", "").upper()
                if "MUSS" in value:
                    return "MUSS"
                elif "KANN" in value:
                    return "KANN"
        return "SOLLTE"

    def _map_typ(self, typ_str: str) -> BSIAnforderungTyp:
        """Map string to BSIAnforderungTyp enum."""
        typ_upper = typ_str.upper()
        if "MUSS" in typ_upper:
            return BSIAnforderungTyp.MUSS
        elif "KANN" in typ_upper:
            return BSIAnforderungTyp.KANN
        return BSIAnforderungTyp.SOLLTE

    def _determine_schutzbedarf(self, typ: BSIAnforderungTyp) -> BSISchutzbedarf:
        """Determine protection level from requirement type."""
        mapping = {
            BSIAnforderungTyp.MUSS: BSISchutzbedarf.basis,
            BSIAnforderungTyp.SOLLTE: BSISchutzbedarf.standard,
            BSIAnforderungTyp.KANN: BSISchutzbedarf.hoch,
        }
        return mapping.get(typ, BSISchutzbedarf.basis)

    def _extract_prose(self, parts: list) -> Optional[str]:
        """Extract prose text from OSCAL parts."""
        for part in parts:
            if "prose" in part:
                return part["prose"]
        return None
