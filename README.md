# Cine Reservas

Módulo interno de gestión de reservas de asientos para una cadena de cines. Backend en FastAPI + SQLAlchemy + Alembic sobre SQL Server; frontend en Angular 22; todo orquestado con Docker Compose.

Para el detalle de negocio y de arquitectura de datos, ver [`docs/analisis.md`](docs/analisis.md) y [`docs/diseño-db.md`](docs/diseño-db.md).

## Requisitos previos

Docker y Docker Compose v2 (comando `docker compose`). Nada más.

## Setup

```bash
git clone <url-del-repo>
cd cine-reservas
cp .env.example .env   # completar con tus propios valores
docker compose up --build
```

## Qué corre automático

Al levantar, el contenedor `api` hace esto solo, sin pasos manuales:

1. Verifica/crea la base de datos si no existe.
2. Aplica migraciones (`alembic upgrade head`).
3. Carga datos de ejemplo (`seed`, idempotente).
4. Arranca el servidor.

## URLs

| Servicio                 | URL                        |
| ------------------------ | -------------------------- |
| Frontend                 | http://localhost:4200      |
| API                      | http://localhost:8000      |
| Swagger (docs de la API) | http://localhost:8000/docs |
| SQL Server               | `localhost:1433`           |

## Usuarios de prueba

El seed carga estos dos usuarios — de ejemplo, no para producción:

| Usuario       | Contraseña     | Rol        |
| ------------- | -------------- | ---------- |
| `admin`       | `Admin123!`    | admin      |
| `taquillero1` | `Taquilla123!` | taquillero |

## Estructura del monorepo

```
cine-reservas/
├── api/     # Backend FastAPI + SQLAlchemy + Alembic (Python)
├── front/   # Frontend Angular 22 (standalone components, pnpm)
├── db/      # Esquema SQL histórico de referencia — no se ejecuta en el arranque real, la fuente de verdad es api/alembic/
└── docs/    # Análisis funcional, diseño de base de datos y bitácora de decisiones técnicas
```

## Decisiones técnicas

Para el razonamiento detrás de las decisiones de arquitectura y los trade-offs evaluados, ver [`docs/bitacora-decisiones.md`](docs/bitacora-decisiones.md).
