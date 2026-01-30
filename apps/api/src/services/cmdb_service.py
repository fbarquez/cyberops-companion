"""
CMDB Service.

Business logic for Configuration Management Database operations.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.cmdb import (
    ConfigurationItem, SoftwareItem, SoftwareInstallation, SoftwareLicense,
    HardwareSpec, AssetLifecycle, AssetRelationship, AssetChange,
    ConfigurationItemType, ConfigurationItemStatus, AssetLifecycleStage,
    RelationshipType, ChangeType, SoftwareCategory, LicenseType
)
from src.models.vulnerability import Asset, AssetType, AssetCriticality
from src.schemas.cmdb import (
    ConfigurationItemCreate, ConfigurationItemUpdate,
    SoftwareItemCreate, SoftwareItemUpdate,
    SoftwareInstallationCreate, SoftwareLicenseCreate,
    HardwareSpecCreate, HardwareSpecUpdate,
    AssetLifecycleCreate, AssetLifecycleUpdate,
    AssetRelationshipCreate, AssetChangeCreate
)

logger = logging.getLogger(__name__)


class CMDBService:
    """Service for CMDB operations."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    # ==================== Configuration Items ====================

    async def generate_ci_id(self, ci_type: ConfigurationItemType) -> str:
        """Generate unique CI ID."""
        prefix = {
            ConfigurationItemType.APPLICATION: "APP",
            ConfigurationItemType.SERVICE: "SVC",
            ConfigurationItemType.DATABASE: "DB",
            ConfigurationItemType.MIDDLEWARE: "MW",
            ConfigurationItemType.OPERATING_SYSTEM: "OS",
            ConfigurationItemType.NETWORK: "NET",
            ConfigurationItemType.STORAGE: "STG",
            ConfigurationItemType.SECURITY: "SEC",
            ConfigurationItemType.INFRASTRUCTURE: "INF",
            ConfigurationItemType.DOCUMENT: "DOC",
        }.get(ci_type, "CI")

        result = await self.db.execute(
            select(func.count(ConfigurationItem.id))
            .where(ConfigurationItem.ci_id.like(f"CI-{prefix}-%"))
        )
        count = result.scalar() or 0
        return f"CI-{prefix}-{str(count + 1).zfill(4)}"

    async def create_configuration_item(
        self,
        data: ConfigurationItemCreate,
        user_id: Optional[str] = None
    ) -> ConfigurationItem:
        """Create a new configuration item."""
        ci_id = await self.generate_ci_id(data.ci_type)

        ci = ConfigurationItem(
            id=str(uuid4()),
            ci_id=ci_id,
            name=data.name,
            display_name=data.display_name,
            description=data.description,
            ci_type=data.ci_type,
            status=ConfigurationItemStatus.PLANNED,
            asset_id=data.asset_id,
            version=data.version,
            configuration=data.configuration,
            baseline_configuration=data.baseline_configuration,
            business_service=data.business_service,
            business_criticality=data.business_criticality,
            sla_tier=data.sla_tier,
            owner=data.owner,
            technical_owner=data.technical_owner,
            department=data.department,
            cost_center=data.cost_center,
            vendor=data.vendor,
            documentation_url=data.documentation_url,
            support_contact=data.support_contact,
            compliance_requirements=data.compliance_requirements,
            data_classification=data.data_classification,
            tags=data.tags,
            go_live_date=data.go_live_date,
            created_by=user_id
        )

        self.db.add(ci)
        await self.db.commit()
        await self.db.refresh(ci)

        logger.info(f"Created CI: {ci.ci_id} - {ci.name}")
        return ci

    async def get_configuration_item(self, ci_id: str) -> Optional[ConfigurationItem]:
        """Get a configuration item by ID."""
        result = await self.db.execute(
            select(ConfigurationItem)
            .options(
                selectinload(ConfigurationItem.software_installations),
                selectinload(ConfigurationItem.change_history)
            )
            .where(or_(ConfigurationItem.id == ci_id, ConfigurationItem.ci_id == ci_id))
        )
        return result.scalar_one_or_none()

    async def list_configuration_items(
        self,
        page: int = 1,
        page_size: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List configuration items with filtering and pagination."""
        query = select(ConfigurationItem)
        count_query = select(func.count(ConfigurationItem.id))

        conditions = []
        if filters:
            if filters.get("search"):
                search = filters["search"]
                conditions.append(or_(
                    ConfigurationItem.name.ilike(f"%{search}%"),
                    ConfigurationItem.ci_id.ilike(f"%{search}%"),
                    ConfigurationItem.description.ilike(f"%{search}%")
                ))
            if filters.get("ci_type"):
                conditions.append(ConfigurationItem.ci_type == filters["ci_type"])
            if filters.get("status"):
                conditions.append(ConfigurationItem.status == filters["status"])
            if filters.get("department"):
                conditions.append(ConfigurationItem.department == filters["department"])
            if filters.get("business_service"):
                conditions.append(ConfigurationItem.business_service == filters["business_service"])

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(desc(ConfigurationItem.created_at)).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return {
            "items": list(items),
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def update_configuration_item(
        self,
        ci_id: str,
        data: ConfigurationItemUpdate,
        user_id: Optional[str] = None
    ) -> Optional[ConfigurationItem]:
        """Update a configuration item."""
        ci = await self.get_configuration_item(ci_id)
        if not ci:
            return None

        # Track changes
        old_state = {
            "name": ci.name,
            "status": ci.status.value if ci.status else None,
            "version": ci.version,
            "configuration": ci.configuration
        }

        update_data = data.model_dump(exclude_unset=True)
        changed_fields = list(update_data.keys())

        for key, value in update_data.items():
            setattr(ci, key, value)

        # Create change record
        if changed_fields:
            new_state = {
                "name": ci.name,
                "status": ci.status.value if ci.status else None,
                "version": ci.version,
                "configuration": ci.configuration
            }
            change = AssetChange(
                id=str(uuid4()),
                ci_id=ci.id,
                change_type=ChangeType.UPDATED,
                change_summary=f"Updated CI: {', '.join(changed_fields)}",
                previous_state=old_state,
                new_state=new_state,
                changed_fields=changed_fields,
                changed_by=user_id
            )
            self.db.add(change)

        await self.db.commit()
        await self.db.refresh(ci)
        return ci

    async def delete_configuration_item(self, ci_id: str) -> bool:
        """Delete a configuration item."""
        ci = await self.get_configuration_item(ci_id)
        if not ci:
            return False

        await self.db.delete(ci)
        await self.db.commit()
        return True

    # ==================== Software Items ====================

    async def create_software_item(
        self,
        data: SoftwareItemCreate
    ) -> SoftwareItem:
        """Create a new software catalog item."""
        software = SoftwareItem(
            id=str(uuid4()),
            name=data.name,
            vendor=data.vendor,
            version=data.version,
            category=data.category,
            description=data.description,
            homepage_url=data.homepage_url,
            license_type=data.license_type,
            license_required=data.license_required,
            is_approved=data.is_approved,
            is_prohibited=data.is_prohibited,
            cpe_id=data.cpe_id,
            end_of_life_date=data.end_of_life_date,
            end_of_support_date=data.end_of_support_date,
            tags=data.tags
        )

        self.db.add(software)
        await self.db.commit()
        await self.db.refresh(software)

        logger.info(f"Created software: {software.name}")
        return software

    async def get_software_item(self, software_id: str) -> Optional[SoftwareItem]:
        """Get a software item by ID."""
        result = await self.db.execute(
            select(SoftwareItem)
            .options(
                selectinload(SoftwareItem.installations),
                selectinload(SoftwareItem.licenses)
            )
            .where(SoftwareItem.id == software_id)
        )
        return result.scalar_one_or_none()

    async def list_software_items(
        self,
        page: int = 1,
        page_size: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List software items with filtering and pagination."""
        query = select(SoftwareItem)
        count_query = select(func.count(SoftwareItem.id))

        conditions = []
        if filters:
            if filters.get("search"):
                search = filters["search"]
                conditions.append(or_(
                    SoftwareItem.name.ilike(f"%{search}%"),
                    SoftwareItem.vendor.ilike(f"%{search}%")
                ))
            if filters.get("category"):
                conditions.append(SoftwareItem.category == filters["category"])
            if filters.get("is_approved") is not None:
                conditions.append(SoftwareItem.is_approved == filters["is_approved"])
            if filters.get("is_prohibited") is not None:
                conditions.append(SoftwareItem.is_prohibited == filters["is_prohibited"])

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(SoftwareItem.name).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        # Add installation count
        items_with_count = []
        for item in items:
            count_result = await self.db.execute(
                select(func.count(SoftwareInstallation.id))
                .where(SoftwareInstallation.software_id == item.id)
            )
            item_dict = {
                **item.__dict__,
                "installation_count": count_result.scalar() or 0
            }
            items_with_count.append(item_dict)

        return {
            "items": items_with_count,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def update_software_item(
        self,
        software_id: str,
        data: SoftwareItemUpdate
    ) -> Optional[SoftwareItem]:
        """Update a software item."""
        software = await self.get_software_item(software_id)
        if not software:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(software, key, value)

        await self.db.commit()
        await self.db.refresh(software)
        return software

    # ==================== Software Installations ====================

    async def create_software_installation(
        self,
        data: SoftwareInstallationCreate
    ) -> SoftwareInstallation:
        """Create a software installation record."""
        installation = SoftwareInstallation(
            id=str(uuid4()),
            software_id=data.software_id,
            asset_id=data.asset_id,
            ci_id=data.ci_id,
            installed_version=data.installed_version,
            installation_path=data.installation_path,
            installation_date=data.installation_date,
            license_id=data.license_id,
            discovered_at=datetime.utcnow(),
            discovery_source=data.discovery_source
        )

        self.db.add(installation)
        await self.db.commit()
        await self.db.refresh(installation)

        logger.info(f"Created software installation: {installation.id}")
        return installation

    async def get_asset_software(self, asset_id: str) -> List[SoftwareInstallation]:
        """Get all software installed on an asset."""
        result = await self.db.execute(
            select(SoftwareInstallation)
            .options(selectinload(SoftwareInstallation.software))
            .where(SoftwareInstallation.asset_id == asset_id)
            .order_by(SoftwareInstallation.created_at)
        )
        return list(result.scalars().all())

    # ==================== Software Licenses ====================

    async def create_software_license(
        self,
        data: SoftwareLicenseCreate
    ) -> SoftwareLicense:
        """Create a software license."""
        license_record = SoftwareLicense(
            id=str(uuid4()),
            software_id=data.software_id,
            license_key=data.license_key,
            license_type=data.license_type,
            license_name=data.license_name,
            total_licenses=data.total_licenses,
            purchase_date=data.purchase_date,
            expiration_date=data.expiration_date,
            cost=data.cost,
            currency=data.currency,
            renewal_cost=data.renewal_cost,
            vendor=data.vendor,
            support_expiration=data.support_expiration,
            contract_reference=data.contract_reference,
            notes=data.notes
        )

        self.db.add(license_record)
        await self.db.commit()
        await self.db.refresh(license_record)

        logger.info(f"Created license: {license_record.id}")
        return license_record

    async def list_software_licenses(
        self,
        page: int = 1,
        page_size: int = 50,
        expiring_soon: bool = False
    ) -> Dict[str, Any]:
        """List software licenses."""
        query = select(SoftwareLicense).options(selectinload(SoftwareLicense.software))
        count_query = select(func.count(SoftwareLicense.id))

        if expiring_soon:
            soon = datetime.utcnow() + timedelta(days=90)
            condition = and_(
                SoftwareLicense.expiration_date.isnot(None),
                SoftwareLicense.expiration_date <= soon,
                SoftwareLicense.is_active == True
            )
            query = query.where(condition)
            count_query = count_query.where(condition)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(SoftwareLicense.expiration_date).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        licenses = result.scalars().all()

        return {
            "licenses": list(licenses),
            "total": total,
            "page": page,
            "page_size": page_size
        }

    # ==================== Hardware Specs ====================

    async def create_hardware_spec(
        self,
        data: HardwareSpecCreate
    ) -> HardwareSpec:
        """Create hardware specifications for an asset."""
        spec = HardwareSpec(
            id=str(uuid4()),
            asset_id=data.asset_id,
            manufacturer=data.manufacturer,
            model=data.model,
            serial_number=data.serial_number,
            asset_tag=data.asset_tag,
            form_factor=data.form_factor,
            rack_location=data.rack_location,
            rack_unit=data.rack_unit,
            cpu_model=data.cpu_model,
            cpu_cores=data.cpu_cores,
            cpu_threads=data.cpu_threads,
            cpu_speed_ghz=data.cpu_speed_ghz,
            ram_gb=data.ram_gb,
            ram_type=data.ram_type,
            ram_slots_total=data.ram_slots_total,
            ram_slots_used=data.ram_slots_used,
            storage_total_gb=data.storage_total_gb,
            storage_type=data.storage_type,
            storage_details=data.storage_details,
            network_interfaces=data.network_interfaces,
            power_supply_watts=data.power_supply_watts,
            power_supplies_count=data.power_supplies_count,
            warranty_start=data.warranty_start,
            warranty_end=data.warranty_end,
            warranty_provider=data.warranty_provider,
            purchase_date=data.purchase_date,
            purchase_cost=data.purchase_cost,
            purchase_vendor=data.purchase_vendor,
            purchase_order=data.purchase_order
        )

        self.db.add(spec)
        await self.db.commit()
        await self.db.refresh(spec)

        logger.info(f"Created hardware spec for asset: {data.asset_id}")
        return spec

    async def get_hardware_spec(self, asset_id: str) -> Optional[HardwareSpec]:
        """Get hardware spec for an asset."""
        result = await self.db.execute(
            select(HardwareSpec).where(HardwareSpec.asset_id == asset_id)
        )
        return result.scalar_one_or_none()

    async def update_hardware_spec(
        self,
        asset_id: str,
        data: HardwareSpecUpdate
    ) -> Optional[HardwareSpec]:
        """Update hardware spec."""
        spec = await self.get_hardware_spec(asset_id)
        if not spec:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(spec, key, value)

        await self.db.commit()
        await self.db.refresh(spec)
        return spec

    # ==================== Asset Lifecycle ====================

    async def create_asset_lifecycle(
        self,
        data: AssetLifecycleCreate
    ) -> AssetLifecycle:
        """Create asset lifecycle record."""
        lifecycle = AssetLifecycle(
            id=str(uuid4()),
            asset_id=data.asset_id,
            current_stage=data.current_stage,
            procurement_date=data.procurement_date,
            expected_end_of_life=data.expected_end_of_life,
            expected_refresh_date=data.expected_refresh_date,
            depreciation_method=data.depreciation_method,
            depreciation_years=data.depreciation_years,
            maintenance_schedule=data.maintenance_schedule,
            maintenance_provider=data.maintenance_provider,
            maintenance_contract=data.maintenance_contract,
            notes=data.notes
        )

        self.db.add(lifecycle)
        await self.db.commit()
        await self.db.refresh(lifecycle)

        logger.info(f"Created lifecycle for asset: {data.asset_id}")
        return lifecycle

    async def get_asset_lifecycle(self, asset_id: str) -> Optional[AssetLifecycle]:
        """Get lifecycle for an asset."""
        result = await self.db.execute(
            select(AssetLifecycle).where(AssetLifecycle.asset_id == asset_id)
        )
        return result.scalar_one_or_none()

    async def update_asset_lifecycle(
        self,
        asset_id: str,
        data: AssetLifecycleUpdate
    ) -> Optional[AssetLifecycle]:
        """Update asset lifecycle."""
        lifecycle = await self.get_asset_lifecycle(asset_id)
        if not lifecycle:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(lifecycle, key, value)

        await self.db.commit()
        await self.db.refresh(lifecycle)
        return lifecycle

    # ==================== Asset Relationships ====================

    async def create_relationship(
        self,
        data: AssetRelationshipCreate,
        user_id: Optional[str] = None
    ) -> AssetRelationship:
        """Create a relationship between assets."""
        relationship = AssetRelationship(
            id=str(uuid4()),
            source_asset_id=data.source_asset_id,
            target_asset_id=data.target_asset_id,
            relationship_type=data.relationship_type,
            description=data.description,
            is_critical=data.is_critical,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
            created_by=user_id
        )

        self.db.add(relationship)
        await self.db.commit()
        await self.db.refresh(relationship)

        logger.info(f"Created relationship: {data.source_asset_id} -> {data.target_asset_id}")
        return relationship

    async def get_asset_relationships(
        self,
        asset_id: str,
        direction: str = "both"
    ) -> List[AssetRelationship]:
        """Get relationships for an asset."""
        conditions = []
        if direction in ("both", "outgoing"):
            conditions.append(AssetRelationship.source_asset_id == asset_id)
        if direction in ("both", "incoming"):
            conditions.append(AssetRelationship.target_asset_id == asset_id)

        result = await self.db.execute(
            select(AssetRelationship)
            .options(
                selectinload(AssetRelationship.source_asset),
                selectinload(AssetRelationship.target_asset)
            )
            .where(or_(*conditions))
            .where(AssetRelationship.is_active == True)
        )
        return list(result.scalars().all())

    async def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship."""
        result = await self.db.execute(
            select(AssetRelationship).where(AssetRelationship.id == relationship_id)
        )
        relationship = result.scalar_one_or_none()
        if not relationship:
            return False

        await self.db.delete(relationship)
        await self.db.commit()
        return True

    # ==================== Asset Changes ====================

    async def record_change(
        self,
        data: AssetChangeCreate,
        user_id: Optional[str] = None
    ) -> AssetChange:
        """Record a change to an asset or CI."""
        change = AssetChange(
            id=str(uuid4()),
            asset_id=data.asset_id,
            ci_id=data.ci_id,
            change_type=data.change_type,
            change_summary=data.change_summary,
            change_description=data.change_description,
            previous_state=data.previous_state,
            new_state=data.new_state,
            changed_fields=data.changed_fields,
            change_ticket=data.change_ticket,
            change_request_id=data.change_request_id,
            approved_by=data.approved_by,
            incident_id=data.incident_id,
            changed_by=user_id
        )

        self.db.add(change)
        await self.db.commit()
        await self.db.refresh(change)

        logger.info(f"Recorded change: {change.change_summary}")
        return change

    async def get_asset_changes(
        self,
        asset_id: Optional[str] = None,
        ci_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Get change history for an asset or CI."""
        query = select(AssetChange)
        count_query = select(func.count(AssetChange.id))

        conditions = []
        if asset_id:
            conditions.append(AssetChange.asset_id == asset_id)
        if ci_id:
            conditions.append(AssetChange.ci_id == ci_id)

        if conditions:
            query = query.where(or_(*conditions))
            count_query = count_query.where(or_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.order_by(desc(AssetChange.changed_at)).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        changes = result.scalars().all()

        return {
            "changes": list(changes),
            "total": total,
            "page": page,
            "page_size": page_size
        }

    # ==================== Dependency Map ====================

    async def get_dependency_map(
        self,
        asset_id: Optional[str] = None,
        ci_id: Optional[str] = None,
        depth: int = 2
    ) -> Dict[str, Any]:
        """Build a dependency map for visualization."""
        nodes = []
        edges = []
        visited = set()

        async def traverse_dependencies(current_id: str, current_depth: int, is_asset: bool = True):
            if current_depth > depth or current_id in visited:
                return
            visited.add(current_id)

            if is_asset:
                # Get asset
                result = await self.db.execute(
                    select(Asset).where(Asset.id == current_id)
                )
                asset = result.scalar_one_or_none()
                if asset:
                    nodes.append({
                        "id": asset.id,
                        "name": asset.name,
                        "type": asset.asset_type.value if asset.asset_type else "unknown",
                        "criticality": asset.criticality.value if asset.criticality else None
                    })

                    # Get relationships
                    relationships = await self.get_asset_relationships(current_id)
                    for rel in relationships:
                        edges.append({
                            "source": rel.source_asset_id,
                            "target": rel.target_asset_id,
                            "relationship_type": rel.relationship_type.value,
                            "is_critical": rel.is_critical
                        })
                        # Traverse connected assets
                        next_id = rel.target_asset_id if rel.source_asset_id == current_id else rel.source_asset_id
                        await traverse_dependencies(next_id, current_depth + 1, is_asset=True)

        if asset_id:
            await traverse_dependencies(asset_id, 0, is_asset=True)

        return {
            "nodes": nodes,
            "edges": edges
        }

    # ==================== Statistics ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """Get CMDB statistics."""
        # Assets
        total_assets = await self.db.execute(select(func.count(Asset.id)))
        active_assets = await self.db.execute(
            select(func.count(Asset.id)).where(Asset.is_active == True)
        )

        # Configuration Items
        total_cis = await self.db.execute(select(func.count(ConfigurationItem.id)))
        production_cis = await self.db.execute(
            select(func.count(ConfigurationItem.id))
            .where(ConfigurationItem.status == ConfigurationItemStatus.PRODUCTION)
        )

        # Software
        total_software = await self.db.execute(select(func.count(SoftwareItem.id)))
        approved_software = await self.db.execute(
            select(func.count(SoftwareItem.id)).where(SoftwareItem.is_approved == True)
        )
        prohibited_software = await self.db.execute(
            select(func.count(SoftwareItem.id)).where(SoftwareItem.is_prohibited == True)
        )

        # Licenses
        total_licenses = await self.db.execute(select(func.count(SoftwareLicense.id)))
        soon = datetime.utcnow() + timedelta(days=90)
        expiring_licenses = await self.db.execute(
            select(func.count(SoftwareLicense.id))
            .where(and_(
                SoftwareLicense.expiration_date.isnot(None),
                SoftwareLicense.expiration_date <= soon,
                SoftwareLicense.is_active == True
            ))
        )

        # Relationships
        total_relationships = await self.db.execute(
            select(func.count(AssetRelationship.id))
            .where(AssetRelationship.is_active == True)
        )

        # Group by queries
        assets_by_type = await self.db.execute(
            select(Asset.asset_type, func.count(Asset.id))
            .where(Asset.is_active == True)
            .group_by(Asset.asset_type)
        )

        assets_by_criticality = await self.db.execute(
            select(Asset.criticality, func.count(Asset.id))
            .where(Asset.is_active == True)
            .group_by(Asset.criticality)
        )

        assets_by_env = await self.db.execute(
            select(Asset.environment, func.count(Asset.id))
            .where(and_(Asset.is_active == True, Asset.environment.isnot(None)))
            .group_by(Asset.environment)
        )

        cis_by_type = await self.db.execute(
            select(ConfigurationItem.ci_type, func.count(ConfigurationItem.id))
            .group_by(ConfigurationItem.ci_type)
        )

        cis_by_status = await self.db.execute(
            select(ConfigurationItem.status, func.count(ConfigurationItem.id))
            .group_by(ConfigurationItem.status)
        )

        software_by_category = await self.db.execute(
            select(SoftwareItem.category, func.count(SoftwareItem.id))
            .where(SoftwareItem.category.isnot(None))
            .group_by(SoftwareItem.category)
        )

        lifecycle_by_stage = await self.db.execute(
            select(AssetLifecycle.current_stage, func.count(AssetLifecycle.id))
            .group_by(AssetLifecycle.current_stage)
        )

        # Recent changes
        recent_changes_result = await self.db.execute(
            select(AssetChange)
            .order_by(desc(AssetChange.changed_at))
            .limit(10)
        )
        recent_changes = recent_changes_result.scalars().all()

        return {
            "total_assets": total_assets.scalar() or 0,
            "active_assets": active_assets.scalar() or 0,
            "total_configuration_items": total_cis.scalar() or 0,
            "production_cis": production_cis.scalar() or 0,
            "total_software_items": total_software.scalar() or 0,
            "approved_software": approved_software.scalar() or 0,
            "prohibited_software": prohibited_software.scalar() or 0,
            "total_licenses": total_licenses.scalar() or 0,
            "expiring_licenses": expiring_licenses.scalar() or 0,
            "total_relationships": total_relationships.scalar() or 0,
            "assets_by_type": {str(row[0].value): row[1] for row in assets_by_type.fetchall() if row[0]},
            "assets_by_criticality": {str(row[0].value): row[1] for row in assets_by_criticality.fetchall() if row[0]},
            "assets_by_environment": {str(row[0]): row[1] for row in assets_by_env.fetchall() if row[0]},
            "cis_by_type": {str(row[0].value): row[1] for row in cis_by_type.fetchall() if row[0]},
            "cis_by_status": {str(row[0].value): row[1] for row in cis_by_status.fetchall() if row[0]},
            "software_by_category": {str(row[0].value): row[1] for row in software_by_category.fetchall() if row[0]},
            "lifecycle_by_stage": {str(row[0].value): row[1] for row in lifecycle_by_stage.fetchall() if row[0]},
            "recent_changes": recent_changes
        }
