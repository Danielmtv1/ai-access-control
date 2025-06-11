import json
from datetime import datetime, timezone
from typing import Optional
from app.domain.entities.door import Door, DoorType, SecurityLevel, DoorStatus, AccessSchedule
from app.infrastructure.database.models.door import DoorModel

class DoorMapper:
    """Mapeador entre entidades de dominio Door y modelos de base de datos"""
    
    @staticmethod
    def to_domain(model: DoorModel) -> Door:
        """Convierte un modelo de base de datos a una entidad de dominio"""
        if not model:
            return None
        
        # Parse default schedule from JSON
        default_schedule = None
        if model.default_schedule:
            try:
                schedule_data = json.loads(model.default_schedule)
                default_schedule = AccessSchedule(
                    days_of_week=schedule_data.get('days_of_week', []),
                    start_time=datetime.strptime(schedule_data.get('start_time', '00:00'), '%H:%M').time(),
                    end_time=datetime.strptime(schedule_data.get('end_time', '23:59'), '%H:%M').time()
                )
            except (json.JSONDecodeError, ValueError, KeyError):
                # If parsing fails, set to None
                default_schedule = None
            
        return Door(
            id=model.id,
            name=model.name,
            location=model.location,
            description=model.description,
            door_type=DoorType(model.door_type),
            security_level=SecurityLevel(model.security_level),
            status=DoorStatus(model.status),
            default_schedule=default_schedule,
            requires_pin=model.requires_pin,
            max_attempts=model.max_attempts,
            lockout_duration=model.lockout_duration,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_access=model.last_access,
            failed_attempts=model.failed_attempts,
            locked_until=model.locked_until
        )
    
    @staticmethod
    def to_model(door: Door) -> DoorModel:
        """Convierte una entidad de dominio a un modelo de base de datos"""
        # Serialize default schedule to JSON
        default_schedule_json = None
        if door.default_schedule:
            default_schedule_json = json.dumps({
                'days_of_week': door.default_schedule.days_of_week,
                'start_time': door.default_schedule.start_time.strftime('%H:%M'),
                'end_time': door.default_schedule.end_time.strftime('%H:%M')
            })
        
        return DoorModel(
            id=door.id,
            name=door.name,
            location=door.location,
            description=door.description,
            door_type=door.door_type.value,
            security_level=door.security_level.value,
            status=door.status.value,
            default_schedule=default_schedule_json,
            requires_pin=door.requires_pin,
            max_attempts=door.max_attempts,
            lockout_duration=door.lockout_duration,
            failed_attempts=door.failed_attempts,
            locked_until=door.locked_until,
            last_access=door.last_access,
            created_at=door.created_at,
            updated_at=door.updated_at
        )
    
    @staticmethod
    def update_model_from_domain(model: DoorModel, door: Door) -> DoorModel:
        """Actualiza un modelo de base de datos con los datos de una entidad de dominio"""
        # Serialize default schedule to JSON
        default_schedule_json = None
        if door.default_schedule:
            default_schedule_json = json.dumps({
                'days_of_week': door.default_schedule.days_of_week,
                'start_time': door.default_schedule.start_time.strftime('%H:%M'),
                'end_time': door.default_schedule.end_time.strftime('%H:%M')
            })
        
        model.name = door.name
        model.location = door.location
        model.description = door.description
        model.door_type = door.door_type.value
        model.security_level = door.security_level.value
        model.status = door.status.value
        model.default_schedule = default_schedule_json
        model.requires_pin = door.requires_pin
        model.max_attempts = door.max_attempts
        model.lockout_duration = door.lockout_duration
        model.failed_attempts = door.failed_attempts
        model.locked_until = door.locked_until
        model.last_access = door.last_access
        model.updated_at = datetime.now(timezone.utc)
        return model