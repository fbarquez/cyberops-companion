"""
CMDB API Endpoints.

REST API for Configuration Management Database operations.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.services.cmdb_service import CMDBService
from src.schemas.cmdb import (
    ConfigurationItemCreate, ConfigurationItemUpdate, ConfigurationItemResponse, ConfigurationItemListResponse,
    SoftwareItemCreate, SoftwareItemUpdate, SoftwareItemResponse, SoftwareItemListResponse,
    SoftwareInstallationCreate, SoftwareInstallationResponse,
    SoftwareLicenseCreate, SoftwareLicenseResponse,
    HardwareSpecCreate, HardwareSpecUpdate, HardwareSpecResponse,
    AssetLifecycleCreate, AssetLifecycleUpdate, AssetLifecycleResponse,
    AssetRelationshipCreate, AssetRelationshipResponse,
    AssetChangeCreate, AssetChangeResponse, AssetChangeListResponse,
    CMDBStats, DependencyMap,
    ConfigurationItemType, ConfigurationItemStatus, SoftwareCategory
)

router = APIRouter(prefix="/cmdb", tags=["CMDB"])


# ==================== Configuration Items ====================

@router.post("/configuration-items", response_model=ConfigurationItemResponse, status_code=status.HTTP_201_CREATED)
async def create_configuration_item(
    data: ConfigurationItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new configuration item."""
    service = CMDBService(db)
    return await service.create_configuration_item(data)


@router.get("/configuration-items", response_model=ConfigurationItemListResponse)
async def list_configuration_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ci_type: Optional[ConfigurationItemType] = None,
    status: Optional[ConfigurationItemStatus] = None,
    department: Optional[str] = None,
    business_service: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List configuration items with filtering and pagination."""
    service = CMDBService(db)
    filters = {}
    if ci_type:
        filters["ci_type"] = ci_type
    if status:
        filters["status"] = status
    if department:
        filters["department"] = department
    if business_service:
        filters["business_service"] = business_service
    if search:
        filters["search"] = search

    return await service.list_configuration_items(page=page, page_size=page_size, filters=filters)


@router.get("/configuration-items/{ci_id}", response_model=ConfigurationItemResponse)
async def get_configuration_item(
    ci_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a configuration item by ID."""
    service = CMDBService(db)
    ci = await service.get_configuration_item(ci_id)
    if not ci:
        raise HTTPException(status_code=404, detail="Configuration item not found")
    return ci


@router.put("/configuration-items/{ci_id}", response_model=ConfigurationItemResponse)
async def update_configuration_item(
    ci_id: str,
    data: ConfigurationItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a configuration item."""
    service = CMDBService(db)
    ci = await service.update_configuration_item(ci_id, data)
    if not ci:
        raise HTTPException(status_code=404, detail="Configuration item not found")
    return ci


@router.delete("/configuration-items/{ci_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_configuration_item(
    ci_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a configuration item."""
    service = CMDBService(db)
    success = await service.delete_configuration_item(ci_id)
    if not success:
        raise HTTPException(status_code=404, detail="Configuration item not found")
    return None


# ==================== Software Items ====================

@router.post("/software", response_model=SoftwareItemResponse, status_code=status.HTTP_201_CREATED)
async def create_software_item(
    data: SoftwareItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new software catalog item."""
    service = CMDBService(db)
    return await service.create_software_item(data)


@router.get("/software", response_model=SoftwareItemListResponse)
async def list_software_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[SoftwareCategory] = None,
    is_approved: Optional[bool] = None,
    is_prohibited: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List software items with filtering and pagination."""
    service = CMDBService(db)
    filters = {}
    if category:
        filters["category"] = category
    if is_approved is not None:
        filters["is_approved"] = is_approved
    if is_prohibited is not None:
        filters["is_prohibited"] = is_prohibited
    if search:
        filters["search"] = search

    return await service.list_software_items(page=page, page_size=page_size, filters=filters)


@router.get("/software/{software_id}", response_model=SoftwareItemResponse)
async def get_software_item(
    software_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a software item by ID."""
    service = CMDBService(db)
    software = await service.get_software_item(software_id)
    if not software:
        raise HTTPException(status_code=404, detail="Software item not found")

    # Get installation count
    from sqlalchemy import select, func
    from src.models.cmdb import SoftwareInstallation
    count_result = await db.execute(
        select(func.count(SoftwareInstallation.id))
        .where(SoftwareInstallation.software_id == software_id)
    )
    software.installation_count = count_result.scalar() or 0
    return software


@router.put("/software/{software_id}", response_model=SoftwareItemResponse)
async def update_software_item(
    software_id: str,
    data: SoftwareItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a software item."""
    service = CMDBService(db)
    software = await service.update_software_item(software_id, data)
    if not software:
        raise HTTPException(status_code=404, detail="Software item not found")
    return software


# ==================== Software Installations ====================

@router.post("/installations", response_model=SoftwareInstallationResponse, status_code=status.HTTP_201_CREATED)
async def create_software_installation(
    data: SoftwareInstallationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a software installation record."""
    service = CMDBService(db)
    installation = await service.create_software_installation(data)

    # Get software name
    software = await service.get_software_item(data.software_id)
    if software:
        installation.software_name = software.name

    return installation


@router.get("/assets/{asset_id}/software", response_model=List[SoftwareInstallationResponse])
async def get_asset_software(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all software installed on an asset."""
    service = CMDBService(db)
    installations = await service.get_asset_software(asset_id)

    # Add software names
    result = []
    for inst in installations:
        inst_dict = {
            "id": inst.id,
            "software_id": inst.software_id,
            "software_name": inst.software.name if inst.software else None,
            "asset_id": inst.asset_id,
            "ci_id": inst.ci_id,
            "installed_version": inst.installed_version,
            "installation_path": inst.installation_path,
            "installation_date": inst.installation_date,
            "is_active": inst.is_active,
            "needs_update": inst.needs_update,
            "latest_available_version": inst.latest_available_version,
            "license_id": inst.license_id,
            "discovered_at": inst.discovered_at,
            "discovery_source": inst.discovery_source,
            "created_at": inst.created_at
        }
        result.append(inst_dict)

    return result


# ==================== Software Licenses ====================

@router.post("/licenses", response_model=SoftwareLicenseResponse, status_code=status.HTTP_201_CREATED)
async def create_software_license(
    data: SoftwareLicenseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a software license."""
    service = CMDBService(db)
    license_record = await service.create_software_license(data)

    # Get software name
    software = await service.get_software_item(data.software_id)
    result = {
        **license_record.__dict__,
        "software_name": software.name if software else None,
        "available_licenses": license_record.total_licenses - license_record.used_licenses,
        "is_expired": license_record.expiration_date < datetime.utcnow() if license_record.expiration_date else False
    }

    return result


@router.get("/licenses")
async def list_software_licenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    expiring_soon: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List software licenses."""
    service = CMDBService(db)
    return await service.list_software_licenses(page=page, page_size=page_size, expiring_soon=expiring_soon)


# ==================== Hardware Specs ====================

@router.post("/hardware", response_model=HardwareSpecResponse, status_code=status.HTTP_201_CREATED)
async def create_hardware_spec(
    data: HardwareSpecCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create hardware specifications for an asset."""
    service = CMDBService(db)
    spec = await service.create_hardware_spec(data)

    # Calculate warranty status
    from datetime import datetime
    if spec.warranty_end:
        if spec.warranty_end < datetime.utcnow():
            spec.warranty_status = "expired"
        elif spec.warranty_end < datetime.utcnow() + timedelta(days=90):
            spec.warranty_status = "expiring_soon"
        else:
            spec.warranty_status = "active"
    else:
        spec.warranty_status = "unknown"

    return spec


@router.get("/assets/{asset_id}/hardware", response_model=HardwareSpecResponse)
async def get_hardware_spec(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get hardware spec for an asset."""
    service = CMDBService(db)
    spec = await service.get_hardware_spec(asset_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Hardware spec not found")

    # Calculate warranty status
    from datetime import datetime, timedelta
    if spec.warranty_end:
        if spec.warranty_end < datetime.utcnow():
            spec.warranty_status = "expired"
        elif spec.warranty_end < datetime.utcnow() + timedelta(days=90):
            spec.warranty_status = "expiring_soon"
        else:
            spec.warranty_status = "active"
    else:
        spec.warranty_status = "unknown"

    return spec


@router.put("/assets/{asset_id}/hardware", response_model=HardwareSpecResponse)
async def update_hardware_spec(
    asset_id: str,
    data: HardwareSpecUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update hardware spec."""
    service = CMDBService(db)
    spec = await service.update_hardware_spec(asset_id, data)
    if not spec:
        raise HTTPException(status_code=404, detail="Hardware spec not found")
    return spec


# ==================== Asset Lifecycle ====================

@router.post("/lifecycle", response_model=AssetLifecycleResponse, status_code=status.HTTP_201_CREATED)
async def create_asset_lifecycle(
    data: AssetLifecycleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create asset lifecycle record."""
    service = CMDBService(db)
    return await service.create_asset_lifecycle(data)


@router.get("/assets/{asset_id}/lifecycle", response_model=AssetLifecycleResponse)
async def get_asset_lifecycle(
    asset_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get lifecycle for an asset."""
    service = CMDBService(db)
    lifecycle = await service.get_asset_lifecycle(asset_id)
    if not lifecycle:
        raise HTTPException(status_code=404, detail="Lifecycle record not found")
    return lifecycle


@router.put("/assets/{asset_id}/lifecycle", response_model=AssetLifecycleResponse)
async def update_asset_lifecycle(
    asset_id: str,
    data: AssetLifecycleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update asset lifecycle."""
    service = CMDBService(db)
    lifecycle = await service.update_asset_lifecycle(asset_id, data)
    if not lifecycle:
        raise HTTPException(status_code=404, detail="Lifecycle record not found")
    return lifecycle


# ==================== Asset Relationships ====================

@router.post("/relationships", response_model=AssetRelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    data: AssetRelationshipCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a relationship between assets."""
    service = CMDBService(db)
    rel = await service.create_relationship(data)

    # Get asset names
    from sqlalchemy import select
    from src.models.vulnerability import Asset

    source_result = await db.execute(select(Asset).where(Asset.id == data.source_asset_id))
    target_result = await db.execute(select(Asset).where(Asset.id == data.target_asset_id))

    source_asset = source_result.scalar_one_or_none()
    target_asset = target_result.scalar_one_or_none()

    return {
        **rel.__dict__,
        "source_asset_name": source_asset.name if source_asset else None,
        "target_asset_name": target_asset.name if target_asset else None
    }


@router.get("/assets/{asset_id}/relationships", response_model=List[AssetRelationshipResponse])
async def get_asset_relationships(
    asset_id: str,
    direction: str = Query("both", regex="^(both|incoming|outgoing)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get relationships for an asset."""
    service = CMDBService(db)
    relationships = await service.get_asset_relationships(asset_id, direction)

    result = []
    for rel in relationships:
        result.append({
            "id": rel.id,
            "source_asset_id": rel.source_asset_id,
            "source_asset_name": rel.source_asset.name if rel.source_asset else None,
            "target_asset_id": rel.target_asset_id,
            "target_asset_name": rel.target_asset.name if rel.target_asset else None,
            "relationship_type": rel.relationship_type,
            "description": rel.description,
            "is_critical": rel.is_critical,
            "is_active": rel.is_active,
            "valid_from": rel.valid_from,
            "valid_to": rel.valid_to,
            "created_at": rel.created_at
        })

    return result


@router.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(
    relationship_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a relationship."""
    service = CMDBService(db)
    success = await service.delete_relationship(relationship_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return None


# ==================== Asset Changes ====================

@router.post("/changes", response_model=AssetChangeResponse, status_code=status.HTTP_201_CREATED)
async def record_change(
    data: AssetChangeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Record a change to an asset or CI."""
    service = CMDBService(db)
    return await service.record_change(data)


@router.get("/changes", response_model=AssetChangeListResponse)
async def list_changes(
    asset_id: Optional[str] = None,
    ci_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List changes with filtering and pagination."""
    service = CMDBService(db)
    return await service.get_asset_changes(asset_id=asset_id, ci_id=ci_id, page=page, page_size=page_size)


@router.get("/assets/{asset_id}/changes", response_model=AssetChangeListResponse)
async def get_asset_changes(
    asset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get change history for an asset."""
    service = CMDBService(db)
    return await service.get_asset_changes(asset_id=asset_id, page=page, page_size=page_size)


# ==================== Dependency Map ====================

@router.get("/assets/{asset_id}/dependencies", response_model=DependencyMap)
async def get_dependency_map(
    asset_id: str,
    depth: int = Query(2, ge=1, le=5),
    db: AsyncSession = Depends(get_db)
):
    """Get dependency map for an asset."""
    service = CMDBService(db)
    return await service.get_dependency_map(asset_id=asset_id, depth=depth)


# ==================== Statistics ====================

@router.get("/statistics", response_model=CMDBStats)
async def get_statistics(
    db: AsyncSession = Depends(get_db)
):
    """Get CMDB statistics."""
    service = CMDBService(db)
    return await service.get_statistics()


# Import datetime and timedelta for license endpoint
from datetime import datetime, timedelta
