#!/bin/bash
chmod +x "$0"

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
print_message() {
    echo -e "${2}${1}${NC}"
}

# Esperar a que la base de datos esté lista
print_message "Esperando a que la base de datos esté lista..." "${YELLOW}"
while ! nc -z db 5432; do
    sleep 0.1
done
print_message "Base de datos lista!" "${GREEN}"

# Instalar dependencias necesarias
print_message "Instalando dependencias..." "${YELLOW}"
pip install uvicorn fastapi alembic sqlalchemy psycopg2-binary

# Ejecutar migraciones
print_message "Ejecutando migraciones de Alembic..." "${YELLOW}"
alembic upgrade head

# Iniciar la aplicación en modo desarrollo
print_message "Iniciando la aplicación en modo desarrollo..." "${GREEN}"
cd /app
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app 