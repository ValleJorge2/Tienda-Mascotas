# Proyecto Mascotas - Microservicios

## 📋 Descripción
Sistema de microservicios para una plataforma de mascotas, implementado con Django REST Framework, RabbitMQ para comunicación entre servicios, y Kong como API Gateway.

## 🔧 Tecnologías Utilizadas

### Backend y Servicios
- **Django REST Framework**: Framework principal para desarrollo de APIs
- **PostgreSQL (Supabase)**: Base de datos centralizada
- **RabbitMQ**: Broker de mensajería para comunicación entre servicios
- **Kong Gateway**: API Gateway para gestión de rutas y balanceo de carga
- **Docker & Docker Compose**: Containerización y orquestación de servicios
- **JWT (JSON Web Tokens)**: Autenticación y seguridad
- **Python 3.10**: Lenguaje de programación base

### Herramientas de Desarrollo
- **Insomnia/Postman**: Testing de APIs
- **Docker Desktop**: Gestión de contenedores
- **Git**: Control de versiones

## 🏗 Arquitectura

### Diagrama de la Arquitectura esta en el archivo core y esta como .png

### Microservicios
1. **Users Service (Puerto: 8006)**
   - Gestión de usuarios
   - Autenticación JWT
   - Registro y login
   - Perfiles de usuario

2. **Products Service (Puerto: 8002)**
   - Catálogo de productos
   - Gestión de inventario
   - Consumidor de eventos de categorías

3. **Categories Service (Puerto: 8005)**
   - Gestión de categorías
   - Publicador de eventos de categorías
   - Taxonomía de productos

4. **Cart Service (Puerto: 8001)**
   - Carrito de compras
   - Gestión de items
   - Consumidor de eventos de productos y categorías

5. **Orders Service (Puerto: 8004)**
   - Procesamiento de órdenes
   - Historial de compras
   - Consumidor de eventos de productos

6. **Reviews Service (Puerto: 8003)**
   - Reseñas de productos
   - Calificaciones
   - Consumidor de eventos de productos

### Patrones de Comunicación
1. **Sincrónica (HTTP/REST)**
   - Comunicación cliente-servidor
   - Endpoints protegidos con JWT
   - Rate limiting implementado en Kong

2. **Asincrónica (RabbitMQ)**
   - Comunicación servicio a servicio
   - Patrones de publicación/suscripción
   - Exchanges de tipo topic para enrutamiento flexible

## 🚀 Instalación y Configuración

### Prerrequisitos
- Docker y Docker Compose instalados
- Git instalado
- Insomnia o Postman (para testing)

### Pasos de Instalación
1. **Clonar el repositorio**
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd mascotas_pruebas/core
2. **Base de datos Supabase**
   una vez que tengas los datos adequados en el core/settings.py DATABASES
   tienes que migrar los models de cada service (nota si te lo pide)
   pasos a seguir para migrar los models:
   1. en la terminal de en donde esta el fichero manage.py commando = python manage.py makemigrations
   2. commando python manage.py migrate
