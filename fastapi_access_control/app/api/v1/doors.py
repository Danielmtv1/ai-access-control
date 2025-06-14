from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import List
from app.domain.entities.door import Door
from app.application.use_cases.door_use_cases import (
    CreateDoorUseCase, GetDoorUseCase, GetDoorByNameUseCase, GetDoorsByLocationUseCase,
    UpdateDoorUseCase, SetDoorStatusUseCase, ListDoorsUseCase, GetActiveDoorsUseCase,
    GetDoorsBySecurityLevelUseCase, DeleteDoorUseCase
)
from app.api.schemas.door_schemas import (
    CreateDoorRequest, UpdateDoorRequest, DoorStatusRequest, DoorResponse, DoorListResponse
)
from app.api.error_handlers import map_domain_error_to_http
from app.api.dependencies.auth_dependencies import get_current_active_user
from app.api.dependencies.repository_dependencies import get_door_repository
from app.ports.door_repository_port import DoorRepositoryPort
from app.config import get_settings
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/doors",
    tags=["Doors"],
    dependencies=[Depends(get_current_active_user)],
    responses={
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Insufficient permissions"},
        422: {"description": "Validation Error - Invalid request data"},
        500: {"description": "Internal Server Error"}
    }
)


@router.post(
    "/",
    response_model=DoorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Door",
    description="""
    Create a new door/access point.
    
    This endpoint creates a new door with the specified details.
    The door can be configured with security levels, access schedules, and other parameters.
    """,
    responses={
        201: {
            "description": "Door created successfully"
        },
        400: {
            "description": "Bad Request - Door name already exists"
        }
    }
)
async def create_door(
    door_data: CreateDoorRequest = Body(..., description="Door creation data"),
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    current_user = Depends(get_current_active_user)
):
    """
    Creates a new door with the specified attributes.
    
    Accepts door details including name, location, type, security level, description, PIN requirements, maximum attempts, lockout duration, and an optional default schedule. Returns the created door's information.
    """
    try:
        logger.info(f"Creating door '{door_data.name}' at location '{door_data.location}'")
        
        # Convert schedule data if provided
        schedule_data = None
        if door_data.default_schedule:
            schedule_data = {
                'days_of_week': door_data.default_schedule.days_of_week,
                'start_time': door_data.default_schedule.start_time,
                'end_time': door_data.default_schedule.end_time
            }
        
        create_door_use_case = CreateDoorUseCase(door_repository)
        door = await create_door_use_case.execute(
            name=door_data.name,
            location=door_data.location,
            door_type=door_data.door_type.value,
            security_level=door_data.security_level.value,
            description=door_data.description,
            requires_pin=door_data.requires_pin,
            max_attempts=door_data.max_attempts,
            lockout_duration=door_data.lockout_duration,
            default_schedule_data=schedule_data
        )
        
        logger.info(f"Door '{door.name}' created successfully with ID {door.id}")
        return DoorResponse.from_entity(door)
        
    except Exception as e:
        logger.error(f"Error creating door: {str(e)}")
        raise map_domain_error_to_http(e)

@router.get(
    "/{door_id}",
    response_model=DoorResponse,
    summary="Get Door by ID",
    description="Retrieve a door by its database ID",
    responses={
        404: {"description": "Door not found"}
    }
)
async def get_door(
    door_id: UUID,
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    current_user = Depends(get_current_active_user)
):
    """
    Retrieves a door by its unique identifier.
    
    Args:
        door_id: The UUID of the door to retrieve.
    
    Returns:
        A DoorResponse object representing the requested door.
    
    Raises:
        An HTTPException if the door is not found or another error occurs.
    """
    try:
        get_door_use_case = GetDoorUseCase(door_repository)
        door = await get_door_use_case.execute(door_id)
        return DoorResponse.from_entity(door)
    except Exception as e:
        logger.error(f"Error getting door {door_id}: {str(e)}")
        raise map_domain_error_to_http(e)

@router.get(
    "/by-name/{name}",
    response_model=DoorResponse,
    summary="Get Door by Name",
    description="Retrieve a door by its name",
    responses={
        404: {"description": "Door not found"}
    }
)
async def get_door_by_name(
    name: str,
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    current_user = Depends(get_current_active_user)
):
    """
    Retrieves a door by its name.
    
    Returns a DoorResponse representing the door with the specified name. Raises an HTTP 404 error if the door is not found.
    """
    try:
        get_door_use_case = GetDoorByNameUseCase(door_repository)
        door = await get_door_use_case.execute(name)
        return DoorResponse.from_entity(door)
    except Exception as e:
        logger.error(f"Error getting door by name '{name}': {str(e)}")
        raise map_domain_error_to_http(e)

@router.get(
    "/location/{location}",
    response_model=List[DoorResponse],
    summary="Get Doors by Location",
    description="Retrieve all doors at a specific location"
)
async def get_doors_by_location(
    location: str,
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    current_user = Depends(get_current_active_user)
):
    """
    Retrieves all doors located at the specified location.
    
    Args:
        location: The location to filter doors by.
    
    Returns:
        A list of DoorResponse objects representing doors at the given location.
    """
    try:
        get_doors_use_case = GetDoorsByLocationUseCase(door_repository)
        doors = await get_doors_use_case.execute(location)
        return [DoorResponse.from_entity(door) for door in doors]
    except Exception as e:
        logger.error(f"Error getting doors for location '{location}': {str(e)}")
        raise map_domain_error_to_http(e)

@router.get(
    "/security-level/{security_level}",
    response_model=List[DoorResponse],
    summary="Get Doors by Security Level",
    description="Retrieve all doors with a specific security level"
)
async def get_doors_by_security_level(
    security_level: str,
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    current_user = Depends(get_current_active_user)
):
    """
    Retrieves all doors with the specified security level.
    
    Args:
        security_level: The security level to filter doors by.
    
    Returns:
        A list of DoorResponse objects representing doors with the given security level.
    """
    try:
        get_doors_use_case = GetDoorsBySecurityLevelUseCase(door_repository)
        doors = await get_doors_use_case.execute(security_level)
        return [DoorResponse.from_entity(door) for door in doors]
    except Exception as e:
        logger.error(f"Error getting doors for security level '{security_level}': {str(e)}")
        raise map_domain_error_to_http(e)

@router.get(
    "/",
    response_model=DoorListResponse,
    summary="List Doors",
    description="List all doors with pagination"
)
async def list_doors(
    skip: int = Query(0, ge=0, description="Number of doors to skip"),
    limit: int = Query(get_settings().DEFAULT_PAGE_SIZE, ge=1, le=get_settings().MAX_PAGE_SIZE, description="Maximum number of doors to return"),
    active_only: bool = Query(False, description="Only return active doors"),
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    current_user = Depends(get_current_active_user)
):
    """
    Retrieves a paginated list of doors, with optional filtering for active doors only.
    
    Args:
        skip: The number of doors to skip for pagination.
        limit: The maximum number of doors to return.
        active_only: If true, only active doors are included in the results.
    
    Returns:
        A DoorListResponse containing the list of doors, total count, skip, and limit.
    """
    try:
        if active_only:
            get_doors_use_case = GetActiveDoorsUseCase(door_repository)
            doors = await get_doors_use_case.execute()
            # Apply pagination manually for active doors
            paginated_doors = doors[skip:skip + limit]
            total = len(doors)
        else:
            list_doors_use_case = ListDoorsUseCase(door_repository)
            doors = await list_doors_use_case.execute(skip, limit)
            paginated_doors = doors
            # Get total count (simplified - in production, you'd want a separate count method)
            total = len(doors) + skip  # This is a simplified approach
        
        return DoorListResponse(
            doors=[DoorResponse.from_entity(door) for door in paginated_doors],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing doors: {str(e)}")
        raise map_domain_error_to_http(e)

@router.put(
    "/{door_id}",
    response_model=DoorResponse,
    summary="Update Door",
    description="Update door information"
)
async def update_door(
    door_id: UUID,
    door_data: UpdateDoorRequest = Body(..., description="Door update data"),
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    current_user = Depends(get_current_active_user)
):
    """
    Updates the details of an existing door by its UUID.
    
    If a default schedule is provided, it is updated along with other door attributes. Returns the updated door information.
    """
    try:
        logger.info(f"Updating door {door_id}")
        
        # Convert schedule data if provided
        schedule_data = None
        if door_data.default_schedule:
            schedule_data = {
                'days_of_week': door_data.default_schedule.days_of_week,
                'start_time': door_data.default_schedule.start_time,
                'end_time': door_data.default_schedule.end_time
            }
        
        update_door_use_case = UpdateDoorUseCase(door_repository)
        door = await update_door_use_case.execute(
            door_id=door_id,
            name=door_data.name,
            location=door_data.location,
            description=door_data.description,
            door_type=door_data.door_type.value if door_data.door_type else None,
            security_level=door_data.security_level.value if door_data.security_level else None,
            requires_pin=door_data.requires_pin,
            max_attempts=door_data.max_attempts,
            lockout_duration=door_data.lockout_duration,
            default_schedule_data=schedule_data
        )
        
        logger.info(f"Door {door_id} updated successfully")
        return DoorResponse.from_entity(door)
        
    except Exception as e:
        logger.error(f"Error updating door {door_id}: {str(e)}")
        raise map_domain_error_to_http(e)

@router.post(
    "/{door_id}/status",
    response_model=DoorResponse,
    summary="Change Door Status",
    description="Change the status of a door (active, maintenance, emergency, etc.)"
)
async def set_door_status(
    door_id: UUID,
    status_data: DoorStatusRequest = Body(..., description="New door status"),
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    current_user = Depends(get_current_active_user)
):
    """
    Updates the status of a door identified by its UUID.
    
    Args:
        door_id: The UUID of the door to update.
        status_data: The new status to set for the door.
    
    Returns:
        The updated door information as a DoorResponse.
    """
    try:
        logger.info(f"Setting door {door_id} status to {status_data.status}")
        
        set_status_use_case = SetDoorStatusUseCase(door_repository)
        door = await set_status_use_case.execute(door_id, status_data.status.value)
        
        logger.info(f"Door {door_id} status updated to {status_data.status}")
        return DoorResponse.from_entity(door)
        
    except Exception as e:
        logger.error(f"Error setting door {door_id} status: {str(e)}")
        raise map_domain_error_to_http(e)

@router.delete(
    "/{door_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Door",
    description="Delete a door permanently"
)
async def delete_door(
    door_id: UUID,
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    current_user = Depends(get_current_active_user)
):
    """
    Deletes a door by its UUID.
    
    Raises a 404 error if the door does not exist.
    """
    try:
        logger.info(f"Deleting door {door_id}")
        
        delete_door_use_case = DeleteDoorUseCase(door_repository)
        deleted = await delete_door_use_case.execute(door_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Door with ID {door_id} not found"
            )
        
        logger.info(f"Door {door_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting door {door_id}: {str(e)}")
        raise map_domain_error_to_http(e)