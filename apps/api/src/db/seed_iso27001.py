"""
ISO 27001:2022 seed script.

Seeds the iso27001_controls table with all 93 controls from Annex A.
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_maker
from src.models.iso27001 import ISO27001Control, ISO27001Theme


# Map theme strings to enum values
THEME_MAP = {
    "A.5": ISO27001Theme.ORGANIZATIONAL,
    "A.6": ISO27001Theme.PEOPLE,
    "A.7": ISO27001Theme.PHYSICAL,
    "A.8": ISO27001Theme.TECHNOLOGICAL,
}


async def seed_iso27001_controls(db: AsyncSession) -> int:
    """
    Seed ISO 27001:2022 controls from JSON file.

    Returns:
        Number of controls seeded
    """
    # Check if already seeded
    result = await db.execute(select(ISO27001Control).limit(1))
    if result.scalar_one_or_none():
        print("ISO 27001:2022 controls already seeded")
        return 0

    # Load JSON data
    data_file = Path(__file__).parent / "data" / "iso27001_2022.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    controls = data.get("controls", [])
    count = 0

    for control_data in controls:
        control = ISO27001Control(
            id=str(uuid4()),
            control_id=control_data["control_id"],
            theme=THEME_MAP[control_data["theme"]],
            sort_order=control_data.get("sort_order", 0),
            title_en=control_data["title_en"],
            title_de=control_data.get("title_de"),
            title_es=control_data.get("title_es"),
            description_en=control_data.get("description_en"),
            description_de=control_data.get("description_de"),
            guidance=control_data.get("guidance"),
            control_type=control_data.get("control_type", []),
            security_properties=control_data.get("security_properties", []),
            cross_references=control_data.get("cross_references", {}),
            created_at=datetime.utcnow(),
        )
        db.add(control)
        count += 1

    await db.flush()
    print(f"Seeded {count} ISO 27001:2022 controls")
    return count


async def verify_iso27001_controls(db: AsyncSession) -> dict:
    """
    Verify the ISO 27001:2022 controls were seeded correctly.

    Returns:
        Dictionary with verification results
    """
    # Count total controls
    result = await db.execute(select(ISO27001Control))
    controls = result.scalars().all()

    # Count by theme
    theme_counts = {}
    for theme in ISO27001Theme:
        theme_result = await db.execute(
            select(ISO27001Control).where(ISO27001Control.theme == theme)
        )
        theme_controls = theme_result.scalars().all()
        theme_counts[theme.value] = len(theme_controls)

    return {
        "total_controls": len(controls),
        "by_theme": theme_counts,
        "expected_total": 93,
        "expected_by_theme": {
            "A.5": 37,
            "A.6": 8,
            "A.7": 14,
            "A.8": 34,
        }
    }


async def run_seed():
    """Run the ISO 27001 seed process."""
    print("Starting ISO 27001:2022 seed...")

    async with async_session_maker() as db:
        try:
            count = await seed_iso27001_controls(db)

            if count > 0:
                # Verify the seed
                verification = await verify_iso27001_controls(db)
                print(f"Verification: {verification}")

                if verification["total_controls"] != verification["expected_total"]:
                    print(f"WARNING: Expected {verification['expected_total']} controls, got {verification['total_controls']}")
                else:
                    print("All controls seeded successfully!")

            await db.commit()
            print("ISO 27001:2022 seed completed!")

        except Exception as e:
            await db.rollback()
            print(f"Error during seed: {e}")
            raise


async def clear_iso27001_controls():
    """Clear all ISO 27001 controls (for testing/reset)."""
    print("Clearing ISO 27001:2022 controls...")

    async with async_session_maker() as db:
        try:
            result = await db.execute(select(ISO27001Control))
            controls = result.scalars().all()

            for control in controls:
                await db.delete(control)

            await db.commit()
            print(f"Cleared {len(controls)} controls")

        except Exception as e:
            await db.rollback()
            print(f"Error during clear: {e}")
            raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        asyncio.run(clear_iso27001_controls())
    else:
        asyncio.run(run_seed())
