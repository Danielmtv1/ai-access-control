"""
Script para crear usuario administrador inicial
Ejecutar después de las migraciones
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger.info(f"Project root: {project_root}")
logger.info(f"Python path: {sys.path}")

from app.config import get_settings
from app.shared.database import AsyncSessionLocal
from app.domain.entities.user import User, Role, UserStatus
from app.domain.services.auth_service import AuthService
from app.infrastructure.persistence.adapters.user_repository import SqlAlchemyUserRepository
from app.application.use_cases.auth_use_cases import CreateUserUseCase
from datetime import datetime, timezone, UTC

async def create_admin_user():
    """Create initial admin user"""
    
    logger.info("🚀 Inicializando usuario administrador...")
    
    try:
        # Setup dependencies
        def db_session_factory():
            return AsyncSessionLocal()
        
        user_repository = SqlAlchemyUserRepository(session_factory=db_session_factory)
        auth_service = AuthService()
        create_user_use_case = CreateUserUseCase(user_repository, auth_service)
        
        # Admin user data
        admin_email = "admin@access-control.com"
        admin_password = "AdminPassword123!"
        admin_name = "System Administrator"
        admin_roles = ["admin", "operator"]
        
        # Check if admin already exists
        existing_admin = await user_repository.get_by_email(admin_email)
        
        if existing_admin:
            logger.info(f"✅ Usuario administrador ya existe: {admin_email}")
            logger.info(f"   Roles: {[role.value for role in existing_admin.roles]}")
            return
        
        # Create admin user
        logger.info(f"📝 Creando usuario administrador: {admin_email}")
        
        admin_user = await create_user_use_case.execute(
            email=admin_email,
            password=admin_password,
            full_name=admin_name,
            roles=admin_roles
        )
        
        logger.info(f"✅ Usuario administrador creado exitosamente!")
        logger.info(f"   ID: {admin_user.id}")
        logger.info(f"   Email: {admin_user.email}")
        logger.info(f"   Roles: {[role.value for role in admin_user.roles]}")
        logger.info(f"   Status: {admin_user.status.value}")
        logger.info("")
        logger.info("🔐 Credenciales de acceso:")
        logger.info(f"   Email: {admin_email}")
        logger.info(f"   Password: {admin_password}")
        logger.info("")
        logger.info("⚠️  IMPORTANTE: Cambia la contraseña después del primer login!")
        
    except Exception as e:
        logger.error(f"❌ Error creando usuario administrador: {str(e)}", exc_info=True)
        raise

async def create_test_users():
    """Create some test users for development"""
    
    logger.info("🧪 Creando usuarios de prueba...")
    
    def db_session_factory():
        return AsyncSessionLocal()
    
    user_repository = SqlAlchemyUserRepository(session_factory=db_session_factory)
    auth_service = AuthService()
    create_user_use_case = CreateUserUseCase(user_repository, auth_service)
    
    test_users = [
        {
            "email": "operator@access-control.com",
            "password": "OperatorPass123!",
            "full_name": "System Operator",
            "roles": ["operator"]
        },
        {
            "email": "viewer@access-control.com", 
            "password": "ViewerPass123!",
            "full_name": "System Viewer",
            "roles": ["viewer"]
        },
        {
            "email": "user@access-control.com",
            "password": "UserPass123!",
            "full_name": "Regular User",
            "roles": ["user"]
        }
    ]
    
    created_count = 0
    
    for user_data in test_users:
        try:
            existing_user = await user_repository.get_by_email(user_data["email"])
            
            if existing_user:
                logger.info(f"   ✅ {user_data['email']} ya existe")
                continue
            
            user = await create_user_use_case.execute(
                email=user_data["email"],
                password=user_data["password"],
                full_name=user_data["full_name"],
                roles=user_data["roles"]
            )
            
            logger.info(f"   ✅ Creado: {user.email} ({user_data['roles']})")
            created_count += 1
            
        except Exception as e:
            logger.error(f"   ❌ Error creando {user_data['email']}: {e}")
    
    logger.info(f"🎉 Usuarios de prueba creados: {created_count}")

async def main():
    """Main initialization function"""
    
    logger.info("=" * 60)
    logger.info("🏗️  INICIALIZACIÓN DEL SISTEMA DE CONTROL DE ACCESO")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        # Create admin user
        await create_admin_user()
        logger.info("")
        
        # Create test users (only in development)
        settings = get_settings()
        if settings.DEBUG:
            await create_test_users()
            logger.info("")
        
        logger.info("✅ Inicialización completada exitosamente!")
        logger.info("")
        logger.info("🚀 Próximos pasos:")
        logger.info("   1. Accede a http://localhost:8000/docs")
        logger.info("   2. Usa POST /api/v1/auth/login para autenticarte")
        logger.info("   3. Copia el access_token de la respuesta")
        logger.info("   4. Haz clic en 'Authorize' en Swagger UI")
        logger.info("   5. Ingresa: Bearer <tu_access_token>")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error en inicialización: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error fatal en la ejecución del script: {str(e)}", exc_info=True)
        sys.exit(1) 