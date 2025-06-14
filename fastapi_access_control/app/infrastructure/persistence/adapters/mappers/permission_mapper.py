from datetime import datetime, timezone
from app.domain.entities.permission import Permission, PermissionStatus
from app.infrastructure.database.models.permission import PermissionModel

class PermissionMapper:
    """Mapeador entre entidades de dominio Permission y modelos de base de datos"""
    
    @staticmethod
    def to_domain(model: PermissionModel) -> Permission:
        """Convierte un modelo de base de datos a una entidad de dominio"""
        if not model:
            return None
            
        return Permission(
            id=model.id,
            user_id=model.user_id,
            door_id=model.door_id,
            card_id=model.card_id,
            status=PermissionStatus(model.status),
            valid_from=model.valid_from,
            valid_until=model.valid_until,
            access_schedule=model.access_schedule,
            pin_required=model.pin_required,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_used=model.last_used
        )
    
    @staticmethod
    def to_model(permission: Permission) -> PermissionModel:
        """Convierte una entidad de dominio a un modelo de base de datos"""
        return PermissionModel(
            id=permission.id,
            user_id=permission.user_id,
            door_id=permission.door_id,
            card_id=permission.card_id,
            status=permission.status.value,
            valid_from=permission.valid_from,
            valid_until=permission.valid_until,
            access_schedule=permission.access_schedule,
            pin_required=permission.pin_required,
            created_by=permission.created_by,
            last_used=permission.last_used,
            created_at=permission.created_at,
            updated_at=permission.updated_at
        )
    
    @staticmethod
    def update_model_from_domain(model: PermissionModel, permission: Permission) -> PermissionModel:
        """Actualiza un modelo de base de datos con los datos de una entidad de dominio"""
        model.user_id = permission.user_id
        model.door_id = permission.door_id
        model.card_id = permission.card_id
        model.status = permission.status.value
        model.valid_from = permission.valid_from
        model.valid_until = permission.valid_until
        model.access_schedule = permission.access_schedule
        model.pin_required = permission.pin_required
        model.created_by = permission.created_by
        model.last_used = permission.last_used
        model.updated_at = datetime.now()
        return model