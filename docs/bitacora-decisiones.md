# Bitácora de decisiones (ADR)

Registro de decisiones técnicas con alternativas reales evaluadas y descartadas. No es un changelog ni un resumen funcional — el contexto de negocio vive en `analisis.md`, y qué hace cada endpoint se lee en el código.

## Índice

- [Concurrencia y datos](#concurrencia-y-datos)
- [Expiración y errores de dominio](#expiración-y-errores-de-dominio)
- [Soft-delete y reglas de negocio](#soft-delete-y-reglas-de-negocio)
- [Tickets y datos de cliente](#tickets-y-datos-de-cliente)
- [Frontend](#frontend)
- [Infraestructura](#infraestructura)
- [Bugs corregidos durante la sesión](#bugs-corregidos-durante-la-sesión-sin-alternativa-de-diseño-real)
- [Sin información suficiente para documentar](#sin-información-suficiente-para-documentar)

---

## Concurrencia y datos

### ADR-01 — Unicidad de asiento vía `ActiveSeatReservation` + `UNIQUE`

**Decisión:** el `UNIQUE(function_id, seat_id)` de motor es la garantía real contra doble reserva, no una validación previa.

**Alternativas descartadas:** `SELECT` previo (condición de carrera); status denormalizado en `ReservationSeat` con índice filtrado (dos fuentes de verdad).

**Con más tiempo:** aplicar el mismo respaldo de constraint al chequeo de aforo.

### ADR-02 — Transacción única en la capa de servicio

**Decisión:** cada operación multi-tabla hace un solo `commit` en el service, nunca en el router.

**Alternativas descartadas:** transacción por router (boilerplate repetido); autocommit implícito por sentencia (deja escrituras a medias).

**Con más tiempo:** decorador/context manager compartido para el patrón try/commit/rollback.

### ADR-03 — No-solapamiento validado en capa de servicio

**Decisión:** `_check_overlap` valida horarios en aplicación, sin respaldo de constraint de motor.

**Alternativas descartadas:** exclusion constraint (SQL Server no lo ofrece).

**Con más tiempo:** tiene condición de carrera real (a diferencia de ADR-01) — falta lock explícito o constraint real.

### ADR-04 — Convención naive-UTC vs columnas timezone-aware

**Decisión:** todo `DateTime` es naive; "naive = UTC" se refuerza a mano en cada borde.

**Alternativas descartadas:** `DATETIMEOFFSET` — evitaba la clase de bugs que encontramos, pero implica migrar columnas ya existentes.

**Con más tiempo:** migrar a `DATETIMEOFFSET` — la convención actual depende de que alguien se acuerde, el tipo no lo fuerza.

**Otras decisiones de esta sección:**
- **Función deshabilitada libera su horario**: `_check_overlap` ahora filtra `is_active=True`; descartado dejarlo sin filtrar porque bloqueaba el horario para siempre.
- **`env_file` resuelto por archivo, no cwd**: fix del bug de resolución por ruta relativa; en Docker es intencionalmente inerte (env vars ya vienen inyectadas), documentado en el código.

---

## Expiración y errores de dominio

### ADR-05 — Expiración perezosa (RF-09) y su límite en vistas agregadas

**Decisión:** `expire_if_needed` corre al leer una reserva individual; no hay proceso periódico. El conteo agregado (`list_functions_with_availability`) filtra por SQL en vez de barrer cada reserva, para no generar escrituras en un endpoint de solo lectura.

**Alternativas descartadas:** cron/job en background (más infraestructura para el alcance actual); sweep completo en el listado (atribuiría cambios de estado a quien solo está mirando).

**Con más tiempo:** un sweep periódico real evitaría que las vistas agregadas muestren ocupación desactualizada.

### ADR-06 — `AppError` con `status_code` por excepción + handler global

**Decisión:** una jerarquía de excepciones con `status_code` propio; un solo handler global las traduce a HTTP.

**Alternativas descartadas:** `try/except` repetido por endpoint (mismo bloque de 3-4 excepts en cada router).

**Con más tiempo:** códigos de error estructurados, no solo mensaje humano.

### ADR-07 — Excepciones `NotFound` consolidadas por dominio dueño

**Decisión:** cada `NotFoundError` se define una vez, en el service dueño, y el resto la importa.

**Alternativas descartadas:** clase duplicada por módulo consumidor (dos fuentes de verdad para el mismo concepto).

**Con más tiempo:** mover las excepciones compartidas a un módulo neutral y eliminar el import diferido que la consolidación forzó.

**Otras decisiones de esta sección:**
- **`GET /reservations` expira antes de filtrar por status**: evita devolver una fila con status ya vencido; descartado filtrar `status` directo en el `WHERE` SQL por el mismo motivo.

---

## Soft-delete y reglas de negocio

### ADR-08 — Guards de disable: bloqueo, y por qué Movie no tiene guard

**Decisión:** `Room`/`MovieFunction` bloquean (409) el disable si hay dependientes activos; `Movie` es incondicional. `MovieFunction.disable` con reservas activas se rechaza en vez de cascadear cancelaciones.

**Alternativas descartadas:** guard también en `Movie` (no aplica, no huerfana nada); cascada automática de cancelación (rompe el principio de que cada cambio de estado sea un acto explícito con su propio actor).

**Con más tiempo:** extraer "bloquear si hay dependientes activos" a un helper compartido.

**Otras decisiones de esta sección:**
- **`is_active` (soft-delete) vs `DELETE` real**: `DELETE` rompería FKs históricas y el objetivo de auditoría; inviable apenas existe una reserva.
- **`RoomUpdate` con `extra="forbid"`**: rechaza explícito (422) en vez de ignorar en silencio campos de layout inmutables (S-04).

---

## Tickets y datos de cliente

### ADR-09 — Formato de `ticket_code`: compuesto legible vs UUID opaco

**Decisión:** `TCK-{reservation_id}-{seat_id}-{random4hex}`, ya único por el `UNIQUE` de `ReservationSeat`.

**Alternativas descartadas:** UUID/random puro — más opaco, ilegible para debug en Swagger.

**Nota:** "un ticket por asiento" ya venía fijado por el modelo antes de esta sesión, no fue una decisión evaluada acá.

### ADR-10 — `customer_email` opcional, sin `EmailStr`

**Decisión:** `str | None` sin validar formato, consistente con `customer_phone`.

**Alternativas descartadas:** `EmailStr` — dependencia extra no instalada, sin envío real de correo que lo justifique (S-12 simula).

**Con más tiempo:** si se integra envío real, ahí sí vale validar formato.

**Otras decisiones de esta sección:**
- **`RESERVATION_HOLD_MINUTES` configurable**: se usa el setting ya existente en `config.py`; descartada una constante local que hubiera duplicado la fuente de verdad.

---

## Frontend

### ADR-11 — Token JWT en `sessionStorage`

**Decisión:** `AuthService` guarda el token en `sessionStorage`.

**Alternativas descartadas:** memoria pura (fuerza re-login en cada F5); `localStorage` (mayor ventana de exposición XSS); cookie `httpOnly` (no viable sin cambiar el backend).

**Con más tiempo:** cookie `httpOnly` + `SameSite` sería la mejora real; nada solo-frontend resuelve XSS de fondo.

### ADR-12 — Funciones del taquillero filtradas 100% client-side

**Decisión:** se trae todo una vez y se filtra por película + rango UTC del día Guatemala en el navegador.

**Alternativas descartadas:** `?date=` del backend — filtra por día calendario UTC, no Guatemala (UTC-6), deja afuera funciones tarde en la noche.

**Con más tiempo:** filtros reales (`movie_id`, rango UTC) en el backend si el catálogo crece.

### ADR-13 — Sin librería de componentes (CSS custom) vs Angular Material

**Decisión:** paleta y componentes propios sobre `_tokens.scss`.

**Alternativas descartadas:** Angular Material — su look default exige más overrides que construir a mano lo necesario.

**Con más tiempo:** reconsiderar si el catálogo de componentes crece mucho.

**Otras decisiones de esta sección:**
- **`qrcode` + wrapper propio vs `angularx-qrcode`**: evita una capa de abstracción extra para un caso de uso mínimo (un `<canvas>`, un input).
- **Formularios inline expandibles vs modal**: evita infraestructura de overlay para 4 formularios simples de creación; se reconsideraría si hubiera flujos que necesiten apilarse.

---

## Infraestructura

### ADR-14 — Imagen Docker fijada a `python:3.12-slim-trixie`

**Decisión:** se fija la versión de Debian en vez de dejar `slim` flotante.

**Alternativas descartadas:** `slim` flotante — causó el break original cuando la etiqueta cambió de SO por debajo sin aviso.

**Con más tiempo:** nada pendiente, ya resuelto de raíz.

---

## Bugs corregidos durante la sesión (sin alternativa de diseño real)

Corregidos porque estaban objetivamente rotos, no porque hubiera una decisión entre dos enfoques igualmente válidos:

- `Column.is_(True)` compila a `IS 1` en T-SQL, sintaxis inválida en SQL Server (`IS` solo es válido con `NULL`) — reemplazado por `Column == True` en los 4 lugares donde aparecía.
- `ENTRYPOINT ["./entrypoint.sh"]` fallaba con `permission denied` porque el bind mount `./api:/app` de docker-compose pisa el `chmod +x` del build — cambiado a `ENTRYPOINT ["sh", "entrypoint.sh"]`.
- `pnpm install`/`ng build` fallaban con `ERR_PNPM_IGNORED_BUILDS` (pnpm 11 bloquea scripts de postinstalación por default) — resuelto con `--config.strict-dep-builds=false` y `ENV PNPM_CONFIG_STRICT_DEP_BUILDS=false` (para la invocación interna de `ng build`). Una alternativa más precisa sería un allow-list de dependencias confiables (`pnpm.onlyBuiltDependencies` en `package.json`) en vez de desactivar el chequeo por completo — no la evaluamos en el momento, queda como pendiente real.
- `StepSeats` leía un `input.required` dentro del constructor — Angular solo lo garantiza resuelto a partir de `ngOnInit`. Movido ahí.
- 6 íconos Unicode (`✕ ✓ ✎ ⏸ ▶ −`) no renderizaban en algunos sistemas/fuentes (tofu boxes) — reemplazados por `<svg>` inline.

## Sin información suficiente para documentar

- **Incidente bcrypt/passlib**: `requirements.txt` fija `bcrypt==4.0.1` junto a `passlib[bcrypt]==1.7.4` (combinación típica del bug conocido donde `passlib` 1.7.4 no reconoce el atributo de versión de `bcrypt` ≥4.1). Este pin ya estaba presente en el primer diff que vi al arrancar la sesión — no participé de ese diagnóstico ni de esa decisión, así que no tengo el razonamiento real para documentarlo acá. Si me contás qué pasó, lo agrego.
