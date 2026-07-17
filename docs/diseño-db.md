# Diseño de Base de Datos — Sistema de Reserva de Boletos de Cine

**Motor:** SQL Server

---

## 1. Entidades

- **Movie**: catálogo de películas.
- **Room**: catálogo de salas.
- **Seat**: distribución fija de asientos por sala.
- **MovieFunction**: función, es decir película + sala + fecha/hora.
- **Reservation**: encabezado de la reserva — cliente, estado, tiempos.
- **ReservationSeat**: historial permanente de qué asientos pertenecieron a cada reserva.
- **ActiveSeatReservation**: ocupación _vigente_ de asientos por función. Es la tabla que garantiza la no-duplicidad de asientos.
- **User**: usuarios internos (admin, taquillero).
- **ReservationStatusHistory**: auditoría de cambios de estado de una reserva.
- **Ticket**: comprobante digital por asiento confirmado.

---

## 2. El problema central: evitar la doble reserva de un asiento (RNF-01)

El requisito no funcional más crítico del sistema es que un asiento nunca quede reservado dos veces para la misma función, incluso si varios taquilleros intentan reservarlo al mismo tiempo (concurrencia, RNF-02).

### 2.1 Por qué no basta con Reservation + ReservationSeat

En una primera versión del modelo, `ReservationSeat` era la única tabla puente entre `Reservation` y `Seat`. El problema: el `status` de la reserva vive en `Reservation`, no en `ReservationSeat`. Un índice único filtrado (`WHERE status IN (...)`) requiere que todas sus columnas —incluida la de filtro— vivan en la misma tabla. Sin esa columna disponible, no había forma de expresar "este asiento solo puede estar activo una vez por función" como un constraint real de base de datos. La única defensa posible habría sido una validación en la capa de aplicación, lo cual reintroduce exactamente la condición de carrera que se buscaba evitar.

### 2.2 Alternativas evaluadas

**Denormalizar `status` dentro de `ReservationSeat` y usar un índice único filtrado** (`WHERE status IN (...)`)
Motivo del descarte: duplica una variable mutable (`status`) en dos tablas, generando dos posibles fuentes de verdad que podrían desincronizarse.

**`UNIQUE(function_id, seat_id)` permanente sobre `ReservationSeat`**
Motivo del descarte: bloquearía el asiento de forma indefinida después de una cancelación, ya que la fila nunca se elimina (tabla histórica). No cumple la regla de negocio de que un asiento cancelado vuelve a estar disponible.

**Solo validación en aplicación** (`SELECT` de disponibilidad antes de `INSERT`, sin constraint)
Motivo del descarte: no resuelve la condición de carrera — dos transacciones pueden leer "disponible" antes de que ninguna haya escrito.

### 2.3 Solución adoptada: tabla ActiveSeatReservation

Se separan dos conceptos que antes convivían en una sola tabla:

**`ReservationSeat`** — historial permanente. Responde "¿qué asientos tuvo esta reserva alguna vez?". Nunca se modifica ni se borra.

**`ActiveSeatReservation`** — ocupación vigente. Responde "¿qué asientos están ocupados _ahora_ para esta función?". Se inserta una fila al crear la reserva; se elimina la fila correspondiente al cancelarse o expirar.

El constraint `UNIQUE(function_id, seat_id)` sobre `ActiveSeatReservation` es simple, sin cláusula `WHERE`, y es la garantía real de RNF-01: si dos taquilleros intentan insertar la misma combinación `(function_id, seat_id)`, el motor acepta la primera y rechaza la segunda por violación de constraint, sin importar el orden en que ambas transacciones hayan leído la disponibilidad previamente. Esto es concurrencia optimista respaldada por el motor de base de datos, no por lógica de aplicación.

### 2.4 El rol de la transacción

El `UNIQUE` resuelve la unicidad del asiento. La transacción resuelve un problema distinto: la atomicidad entre tablas. Crear una reserva implica escribir en `Reservation`, `ReservationSeat` y `ActiveSeatReservation`. Si esas tres escrituras no ocurren dentro de una única transacción, una falla a mitad de camino (por ejemplo, en el tercer insert) podría dejar una `Reservation` sin su correspondiente fila en `ActiveSeatReservation`, desincronizando el modelo — no porque dos personas compitieron por el mismo asiento, sino porque una operación individual quedó a medias.

Por esta razón, toda operación de creación o cambio de estado de una reserva se implementa en la capa de servicio (`ReservationService`) dentro de un único `BEGIN TRANSACTION ... COMMIT`, con `ROLLBACK` ante cualquier error. El acceso directo a las tablas por fuera de esta capa de servicio queda fuera del alcance del sistema.

---

## 3. Otras decisiones relevantes del modelo

**MovieFunction.end_datetime**: se calcula y almacena como fotografía histórica (`start_datetime + Movie.duration_min`) en el momento de crear la función, no se recalcula si `Movie.duration_min` cambia después. Evita que editar una película altere retroactivamente funciones ya programadas.

**No-solapamiento de funciones en la misma sala**: SQL Server no ofrece exclusion constraints nativos como PostgreSQL para validar rangos de tiempo que no se crucen. Esta regla se valida en la capa de servicio, mediante una consulta de rango dentro de la misma transacción de creación de la función.

**Ticket**: referencia `ReservationSeat` (histórico), no `ActiveSeatReservation` (vigente) — el ticket es un comprobante que debe seguir existiendo aunque la reserva cambie de estado más adelante; no tiene ciclo de vida propio, depende del estado de la `Reservation` a la que pertenece.

**ReservationStatusHistory**: registra cada transición de estado (`from_status`, `to_status`, `changed_by`, `changed_at`), cubriendo el requisito de auditoría (RNF-05).

**User.password**: se almacena como hash (bcrypt), nunca en texto plano.

---

## 4. Normalización

El modelo está en 3FN, con una única excepción intencional y documentada: `ReservationSeat.function_id` es denormalizado (derivable vía `Reservation.function_id`). Se conserva para facilitar consultas históricas sin requerir un JOIN adicional con `Reservation`, y porque `ActiveSeatReservation` —que sí necesita `function_id` para su constraint de unicidad— se puebla a partir de los mismos datos en el momento de creación de la reserva.

Esta desviación, junto con las alternativas descartadas de la sección 2.2, se documenta en detalle en la bitácora de decisiones (ADR de concurrencia).
