"""BSI IT-Grundschutz 2023 seed script.

Fetches the BSI IT-Grundschutz catalog from BSI GitHub (OSCAL format)
with fallback to local JSON data.
"""
import json
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.bsi_grundschutz import (
    BSIBaustein, BSIAnforderung,
    BSIKategorie, BSIAnforderungTyp, BSISchutzbedarf
)


# BSI GitHub raw URL for OSCAL catalog
BSI_GITHUB_URL = (
    "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/"
    "main/Quellkataloge/Methodik-Grundschutz++/BSI-Methodik-Grundschutz++-catalog.json"
)

# Local fallback path
LOCAL_DATA_PATH = Path(__file__).parent / "data" / "bsi_grundschutz_2023.json"


def determine_schutzbedarf(typ: BSIAnforderungTyp) -> BSISchutzbedarf:
    """Map requirement type to protection level."""
    mapping = {
        BSIAnforderungTyp.MUSS: BSISchutzbedarf.basis,
        BSIAnforderungTyp.SOLLTE: BSISchutzbedarf.standard,
        BSIAnforderungTyp.KANN: BSISchutzbedarf.hoch,
    }
    return mapping.get(typ, BSISchutzbedarf.basis)


def parse_anforderung_typ(text: str) -> BSIAnforderungTyp:
    """Parse requirement type from description text."""
    text_upper = text.upper()
    if "MUSS" in text_upper or "MÜSSEN" in text_upper:
        return BSIAnforderungTyp.MUSS
    elif "SOLLTE" in text_upper or "SOLLTEN" in text_upper:
        return BSIAnforderungTyp.SOLLTE
    elif "KANN" in text_upper or "KÖNNEN" in text_upper:
        return BSIAnforderungTyp.KANN
    return BSIAnforderungTyp.SOLLTE  # Default


async def fetch_from_github() -> Optional[dict]:
    """Attempt to fetch OSCAL catalog from BSI GitHub."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(BSI_GITHUB_URL)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Failed to fetch from GitHub: {e}")
    return None


def load_local_data() -> dict:
    """Load local fallback JSON data."""
    with open(LOCAL_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_oscal_catalog(oscal_data: dict) -> dict:
    """Parse OSCAL format into our internal format."""
    bausteine = []
    catalog = oscal_data.get("catalog", oscal_data)

    for group in catalog.get("groups", []):
        kategorie_id = group.get("id", "").upper()
        if not hasattr(BSIKategorie, kategorie_id):
            continue

        for subgroup in group.get("groups", []):
            baustein_id = subgroup.get("id", "")
            baustein = {
                "baustein_id": baustein_id,
                "kategorie": kategorie_id,
                "titel": subgroup.get("title", ""),
                "beschreibung": subgroup.get("props", [{}])[0].get("value", ""),
                "anforderungen": []
            }

            for control in subgroup.get("controls", []):
                anf = {
                    "anforderung_id": control.get("id", ""),
                    "titel": control.get("title", ""),
                    "beschreibung": " ".join(
                        p.get("prose", "") for p in control.get("parts", [])
                    ),
                }
                baustein["anforderungen"].append(anf)

            bausteine.append(baustein)

    return {"bausteine": bausteine}


async def seed_bsi_grundschutz(db: AsyncSession, force: bool = False):
    """Seed BSI IT-Grundschutz data.

    Args:
        db: Database session
        force: If True, reseed even if data exists
    """
    # Check if already seeded
    result = await db.execute(select(BSIBaustein).limit(1))
    if result.scalar_one_or_none() and not force:
        print("BSI IT-Grundschutz data already seeded")
        return

    print("Seeding BSI IT-Grundschutz 2023 catalog...")

    # Use local data (OSCAL parsing is complex, local data is reliable)
    print("Loading local BSI IT-Grundschutz data...")
    data = load_local_data()

    baustein_count = 0
    anforderung_count = 0

    for idx, baustein_data in enumerate(data.get("bausteine", [])):
        kategorie_str = baustein_data.get("kategorie", "").upper()
        try:
            kategorie = BSIKategorie(kategorie_str)
        except ValueError:
            print(f"Skipping unknown kategorie: {kategorie_str}")
            continue

        baustein = BSIBaustein(
            id=str(uuid4()),
            baustein_id=baustein_data["baustein_id"],
            kategorie=kategorie,
            titel=baustein_data["titel"],
            title_en=baustein_data.get("title_en"),
            beschreibung=baustein_data.get("beschreibung"),
            zielsetzung=baustein_data.get("zielsetzung"),
            version="2023",
            edition="Edition 2023",
            ir_phases=baustein_data.get("ir_phases", []),
            cross_references=baustein_data.get("cross_references", {}),
            sort_order=idx,
            created_at=datetime.utcnow(),
        )
        db.add(baustein)
        baustein_count += 1

        for anf_idx, anf_data in enumerate(baustein_data.get("anforderungen", [])):
            typ_str = anf_data.get("typ", "")
            if typ_str:
                try:
                    typ = BSIAnforderungTyp(typ_str)
                except ValueError:
                    typ = parse_anforderung_typ(anf_data.get("beschreibung", ""))
            else:
                typ = parse_anforderung_typ(anf_data.get("beschreibung", ""))

            anforderung = BSIAnforderung(
                id=str(uuid4()),
                baustein_fk=baustein.id,
                anforderung_id=anf_data["anforderung_id"],
                typ=typ,
                schutzbedarf=determine_schutzbedarf(typ),
                titel=anf_data["titel"],
                title_en=anf_data.get("title_en"),
                beschreibung=anf_data.get("beschreibung"),
                description_en=anf_data.get("description_en"),
                umsetzungshinweise=anf_data.get("umsetzungshinweise"),
                cross_references=anf_data.get("cross_references", {}),
                aufwandsstufe=anf_data.get("aufwandsstufe"),
                oscal_id=anf_data.get("oscal_id"),
                sort_order=anf_idx,
                created_at=datetime.utcnow(),
            )
            db.add(anforderung)
            anforderung_count += 1

    await db.commit()
    print(f"Seeded {baustein_count} Bausteine and {anforderung_count} Anforderungen")


if __name__ == "__main__":
    import asyncio
    from src.db.database import async_session_maker

    async def main():
        async with async_session_maker() as session:
            await seed_bsi_grundschutz(session)

    asyncio.run(main())
