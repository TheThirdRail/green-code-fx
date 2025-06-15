"""
Green-Code FX Collaboration Manager
Handles shareable links, preset collections, and team workspace features
"""

import json
import time
import uuid
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import quote, unquote

try:
    from .config import config
    import structlog
except ImportError:
    from config import config
    import structlog

logger = structlog.get_logger()


@dataclass
class ShareableLink:
    """Represents a shareable configuration link."""
    link_id: str
    title: str
    description: str
    configuration: Dict[str, Any]
    created_by: str
    created_at: str
    expires_at: Optional[str] = None
    access_count: int = 0
    max_access_count: Optional[int] = None
    is_public: bool = True
    password_hash: Optional[str] = None


@dataclass
class PresetCollection:
    """Represents a collection of presets for team sharing."""
    collection_id: str
    name: str
    description: str
    presets: List[Dict[str, Any]]
    created_by: str
    created_at: str
    updated_at: str
    version: int = 1
    is_public: bool = False
    team_id: Optional[str] = None
    tags: List[str] = None


@dataclass
class TeamWorkspace:
    """Represents a team workspace for collaboration."""
    workspace_id: str
    name: str
    description: str
    created_by: str
    created_at: str
    updated_at: str
    members: List[Dict[str, str]]  # [{"user_id": str, "role": str, "joined_at": str}]
    preset_collections: List[str]  # Collection IDs
    shared_links: List[str]  # Link IDs
    settings: Dict[str, Any]


class CollaborationManager:
    """Manages collaborative features including shareable links and team workspaces."""
    
    def __init__(self):
        """Initialize collaboration manager."""
        self.storage_dir = config.OUTPUT_DIR / "collaboration"
        self.storage_dir.mkdir(exist_ok=True)
        
        self.links_dir = self.storage_dir / "links"
        self.collections_dir = self.storage_dir / "collections"
        self.workspaces_dir = self.storage_dir / "workspaces"
        
        for dir_path in [self.links_dir, self.collections_dir, self.workspaces_dir]:
            dir_path.mkdir(exist_ok=True)
        
        logger.info("Collaboration manager initialized")
    
    # ============================================================================
    # Shareable Links Management
    # ============================================================================
    
    def create_shareable_link(self, title: str, description: str, configuration: Dict[str, Any],
                            created_by: str = "anonymous", expires_hours: Optional[int] = None,
                            max_access_count: Optional[int] = None, password: Optional[str] = None) -> str:
        """
        Create a shareable link for a configuration.
        
        Args:
            title: Link title
            description: Link description
            configuration: Configuration data to share
            created_by: User who created the link
            expires_hours: Hours until link expires (None for no expiration)
            max_access_count: Maximum number of accesses (None for unlimited)
            password: Optional password protection
            
        Returns:
            Shareable URL
        """
        link_id = f"link_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Calculate expiration time
        expires_at = None
        if expires_hours:
            expires_at = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        
        # Hash password if provided
        password_hash = None
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create shareable link object
        shareable_link = ShareableLink(
            link_id=link_id,
            title=title,
            description=description,
            configuration=configuration,
            created_by=created_by,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            max_access_count=max_access_count,
            password_hash=password_hash
        )
        
        # Save to storage
        self._save_shareable_link(shareable_link)
        
        # Generate shareable URL
        encoded_config = self._encode_configuration(configuration)
        share_url = f"/share/{link_id}?config={encoded_config}"
        
        logger.info("Shareable link created", link_id=link_id, title=title, 
                   expires_at=expires_at, created_by=created_by)
        
        return share_url
    
    def access_shareable_link(self, link_id: str, password: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Access a shareable link and return its configuration.
        
        Args:
            link_id: Link identifier
            password: Password if link is protected
            
        Returns:
            Configuration data or None if access denied
        """
        shareable_link = self._load_shareable_link(link_id)
        if not shareable_link:
            return None
        
        # Check expiration
        if shareable_link.expires_at:
            expires_at = datetime.fromisoformat(shareable_link.expires_at)
            if datetime.now() > expires_at:
                logger.warning("Shareable link expired", link_id=link_id)
                return None
        
        # Check access count
        if shareable_link.max_access_count:
            if shareable_link.access_count >= shareable_link.max_access_count:
                logger.warning("Shareable link access limit exceeded", link_id=link_id)
                return None
        
        # Check password
        if shareable_link.password_hash:
            if not password:
                return {"error": "password_required"}
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != shareable_link.password_hash:
                logger.warning("Invalid password for shareable link", link_id=link_id)
                return {"error": "invalid_password"}
        
        # Increment access count
        shareable_link.access_count += 1
        self._save_shareable_link(shareable_link)
        
        logger.info("Shareable link accessed", link_id=link_id, 
                   access_count=shareable_link.access_count)
        
        return {
            "title": shareable_link.title,
            "description": shareable_link.description,
            "configuration": shareable_link.configuration,
            "created_by": shareable_link.created_by,
            "created_at": shareable_link.created_at
        }
    
    def list_shareable_links(self, created_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """List shareable links, optionally filtered by creator."""
        links = []
        
        for link_file in self.links_dir.glob("*.json"):
            try:
                shareable_link = self._load_shareable_link(link_file.stem)
                if shareable_link:
                    if created_by and shareable_link.created_by != created_by:
                        continue
                    
                    links.append({
                        "link_id": shareable_link.link_id,
                        "title": shareable_link.title,
                        "description": shareable_link.description,
                        "created_by": shareable_link.created_by,
                        "created_at": shareable_link.created_at,
                        "expires_at": shareable_link.expires_at,
                        "access_count": shareable_link.access_count,
                        "max_access_count": shareable_link.max_access_count,
                        "is_public": shareable_link.is_public,
                        "has_password": bool(shareable_link.password_hash)
                    })
            except Exception as e:
                logger.error("Failed to load shareable link", file=str(link_file), error=str(e))
        
        return sorted(links, key=lambda x: x["created_at"], reverse=True)
    
    def delete_shareable_link(self, link_id: str, created_by: Optional[str] = None) -> bool:
        """Delete a shareable link."""
        shareable_link = self._load_shareable_link(link_id)
        if not shareable_link:
            return False
        
        # Check ownership if specified
        if created_by and shareable_link.created_by != created_by:
            return False
        
        link_file = self.links_dir / f"{link_id}.json"
        try:
            link_file.unlink()
            logger.info("Shareable link deleted", link_id=link_id)
            return True
        except Exception as e:
            logger.error("Failed to delete shareable link", link_id=link_id, error=str(e))
            return False
    
    # ============================================================================
    # Preset Collections Management
    # ============================================================================
    
    def create_preset_collection(self, name: str, description: str, presets: List[Dict[str, Any]],
                                created_by: str = "anonymous", team_id: Optional[str] = None,
                                is_public: bool = False, tags: Optional[List[str]] = None) -> str:
        """Create a new preset collection."""
        collection_id = f"collection_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        preset_collection = PresetCollection(
            collection_id=collection_id,
            name=name,
            description=description,
            presets=presets,
            created_by=created_by,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            team_id=team_id,
            is_public=is_public,
            tags=tags or []
        )
        
        self._save_preset_collection(preset_collection)
        
        logger.info("Preset collection created", collection_id=collection_id, 
                   name=name, preset_count=len(presets))
        
        return collection_id
    
    def get_preset_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """Get a preset collection by ID."""
        collection = self._load_preset_collection(collection_id)
        if collection:
            return asdict(collection)
        return None
    
    def list_preset_collections(self, team_id: Optional[str] = None, 
                               created_by: Optional[str] = None,
                               include_public: bool = True) -> List[Dict[str, Any]]:
        """List preset collections with optional filtering."""
        collections = []
        
        for collection_file in self.collections_dir.glob("*.json"):
            try:
                collection = self._load_preset_collection(collection_file.stem)
                if collection:
                    # Apply filters
                    if team_id and collection.team_id != team_id:
                        continue
                    if created_by and collection.created_by != created_by:
                        continue
                    if not include_public and collection.is_public:
                        continue
                    
                    collections.append({
                        "collection_id": collection.collection_id,
                        "name": collection.name,
                        "description": collection.description,
                        "preset_count": len(collection.presets),
                        "created_by": collection.created_by,
                        "created_at": collection.created_at,
                        "updated_at": collection.updated_at,
                        "version": collection.version,
                        "is_public": collection.is_public,
                        "team_id": collection.team_id,
                        "tags": collection.tags
                    })
            except Exception as e:
                logger.error("Failed to load preset collection", file=str(collection_file), error=str(e))
        
        return sorted(collections, key=lambda x: x["updated_at"], reverse=True)

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _encode_configuration(self, configuration: Dict[str, Any]) -> str:
        """Encode configuration for URL sharing."""
        try:
            json_str = json.dumps(configuration, separators=(',', ':'))
            encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
            return quote(encoded)
        except Exception as e:
            logger.error("Failed to encode configuration", error=str(e))
            return ""

    def _decode_configuration(self, encoded_config: str) -> Optional[Dict[str, Any]]:
        """Decode configuration from URL."""
        try:
            decoded = unquote(encoded_config)
            json_str = base64.urlsafe_b64decode(decoded.encode()).decode()
            return json.loads(json_str)
        except Exception as e:
            logger.error("Failed to decode configuration", error=str(e))
            return None

    def _save_shareable_link(self, shareable_link: ShareableLink):
        """Save shareable link to storage."""
        try:
            link_file = self.links_dir / f"{shareable_link.link_id}.json"
            with open(link_file, 'w') as f:
                json.dump(asdict(shareable_link), f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save shareable link",
                        link_id=shareable_link.link_id, error=str(e))

    def _load_shareable_link(self, link_id: str) -> Optional[ShareableLink]:
        """Load shareable link from storage."""
        try:
            link_file = self.links_dir / f"{link_id}.json"
            if not link_file.exists():
                return None

            with open(link_file, 'r') as f:
                data = json.load(f)

            return ShareableLink(**data)
        except Exception as e:
            logger.error("Failed to load shareable link", link_id=link_id, error=str(e))
            return None

    def _save_preset_collection(self, collection: PresetCollection):
        """Save preset collection to storage."""
        try:
            collection_file = self.collections_dir / f"{collection.collection_id}.json"
            with open(collection_file, 'w') as f:
                json.dump(asdict(collection), f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save preset collection",
                        collection_id=collection.collection_id, error=str(e))

    def _load_preset_collection(self, collection_id: str) -> Optional[PresetCollection]:
        """Load preset collection from storage."""
        try:
            collection_file = self.collections_dir / f"{collection_id}.json"
            if not collection_file.exists():
                return None

            with open(collection_file, 'r') as f:
                data = json.load(f)

            return PresetCollection(**data)
        except Exception as e:
            logger.error("Failed to load preset collection",
                        collection_id=collection_id, error=str(e))
            return None

    # ============================================================================
    # Export/Import Functionality
    # ============================================================================

    def export_settings(self, settings: Dict[str, Any], include_presets: bool = True,
                       include_history: bool = False) -> Dict[str, Any]:
        """Export settings and optionally presets and history."""
        export_data = {
            "export_version": "1.0",
            "export_timestamp": datetime.now().isoformat(),
            "settings": settings
        }

        if include_presets:
            # Export user's preset collections
            collections = self.list_preset_collections(created_by=settings.get("user_id"))
            export_data["preset_collections"] = collections

        if include_history:
            # Export shareable links created by user
            links = self.list_shareable_links(created_by=settings.get("user_id"))
            export_data["shareable_links"] = links

        return export_data

    def import_settings(self, import_data: Dict[str, Any],
                       user_id: str = "anonymous") -> Dict[str, Any]:
        """Import settings with conflict resolution."""
        result = {
            "success": True,
            "imported_settings": False,
            "imported_collections": 0,
            "imported_links": 0,
            "conflicts": [],
            "errors": []
        }

        try:
            # Validate import data
            if "export_version" not in import_data:
                result["errors"].append("Invalid export format")
                result["success"] = False
                return result

            # Import settings
            if "settings" in import_data:
                # Here you would merge with existing settings
                result["imported_settings"] = True

            # Import preset collections
            if "preset_collections" in import_data:
                for collection_data in import_data["preset_collections"]:
                    try:
                        # Create new collection with new ID
                        new_id = self.create_preset_collection(
                            name=f"Imported: {collection_data['name']}",
                            description=collection_data.get("description", ""),
                            presets=collection_data.get("presets", []),
                            created_by=user_id,
                            tags=collection_data.get("tags", [])
                        )
                        result["imported_collections"] += 1
                    except Exception as e:
                        result["errors"].append(f"Failed to import collection: {str(e)}")

            # Import shareable links
            if "shareable_links" in import_data:
                for link_data in import_data["shareable_links"]:
                    try:
                        # Create new shareable link
                        self.create_shareable_link(
                            title=f"Imported: {link_data['title']}",
                            description=link_data.get("description", ""),
                            configuration=link_data.get("configuration", {}),
                            created_by=user_id
                        )
                        result["imported_links"] += 1
                    except Exception as e:
                        result["errors"].append(f"Failed to import link: {str(e)}")

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Import failed: {str(e)}")

        return result

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def cleanup_expired_links(self):
        """Clean up expired shareable links."""
        cleaned_count = 0

        for link_file in self.links_dir.glob("*.json"):
            try:
                shareable_link = self._load_shareable_link(link_file.stem)
                if shareable_link and shareable_link.expires_at:
                    expires_at = datetime.fromisoformat(shareable_link.expires_at)
                    if datetime.now() > expires_at:
                        link_file.unlink()
                        cleaned_count += 1
                        logger.info("Expired shareable link cleaned up",
                                  link_id=shareable_link.link_id)
            except Exception as e:
                logger.error("Failed to cleanup link", file=str(link_file), error=str(e))

        if cleaned_count > 0:
            logger.info("Cleanup completed", cleaned_links=cleaned_count)

    def get_collaboration_stats(self) -> Dict[str, Any]:
        """Get collaboration system statistics."""
        stats = {
            "total_shareable_links": len(list(self.links_dir.glob("*.json"))),
            "total_preset_collections": len(list(self.collections_dir.glob("*.json"))),
            "total_workspaces": len(list(self.workspaces_dir.glob("*.json"))),
            "active_links": 0,
            "expired_links": 0,
            "public_collections": 0,
            "private_collections": 0
        }

        # Count active vs expired links
        for link_file in self.links_dir.glob("*.json"):
            try:
                shareable_link = self._load_shareable_link(link_file.stem)
                if shareable_link:
                    if shareable_link.expires_at:
                        expires_at = datetime.fromisoformat(shareable_link.expires_at)
                        if datetime.now() > expires_at:
                            stats["expired_links"] += 1
                        else:
                            stats["active_links"] += 1
                    else:
                        stats["active_links"] += 1
            except Exception:
                pass

        # Count public vs private collections
        for collection_file in self.collections_dir.glob("*.json"):
            try:
                collection = self._load_preset_collection(collection_file.stem)
                if collection:
                    if collection.is_public:
                        stats["public_collections"] += 1
                    else:
                        stats["private_collections"] += 1
            except Exception:
                pass

        return stats


# Global collaboration manager instance
collaboration_manager = CollaborationManager()
