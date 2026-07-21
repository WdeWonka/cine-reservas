# Documento de Análisis — Sistema de Reserva de Boletos de Cine

**Proyecto:** Módulo interno de gestión de reservas de asientos para cadena de cines
**Versión:** 3.3 (final)
**Fecha:** Julio 2026

---

## 1. Introducción

Este documento presenta el análisis funcional del módulo interno de reserva de asientos solicitado en el enunciado. Su propósito es dejar explícitos el entendimiento del negocio, los supuestos adoptados ante información no provista, las reglas de negocio identificadas, los requerimientos y las preguntas que quedan abiertas hacia el cliente.

El enunciado es intencionalmente incompleto en varios puntos operativos. Este documento declara con criterio cómo se interpretó cada vacío, de forma que sea auditable y ajustable si el negocio real difiere de lo asumido. Cubre el entendimiento del problema, no el razonamiento técnico detrás de cómo se implementó cada mecanismo — eso, junto con las alternativas descartadas, se documenta en la **bitácora de decisiones**.

---

## 2. Contexto y alcance

### 2.1 Descripción del problema

Una cadena de cines necesita un módulo interno para gestionar la reserva de asientos en sus funciones. Cada sala tiene una distribución fija de asientos. Se programan funciones (una película, en una sala, a una fecha y hora determinada). Los clientes reservan uno o más asientos para una función, y la reserva pasa por varios estados hasta utilizarse o cancelarse.

### 2.2 Dentro del alcance

- Gestión de un catálogo mínimo de películas, salas y funciones.
- Consulta de disponibilidad de asientos por función.
- Creación de reservas (uno o más asientos) a nombre de un cliente.
- Cambio de estado de una reserva, respetando transiciones válidas.
- Expiración automática de reservas no confirmadas dentro de un tiempo límite.
- Reporte de taquilla por función.
- Dos roles de acceso: administrador y taquillero.
- Generación de un comprobante digital por asiento confirmado (Ticket), como extensión del MVP.

### 2.3 Fuera de alcance

- Procesamiento de pagos o medios de pago.
- Facturación fiscal o emisión de comprobantes tributarios.
- Integración real con servicios externos de mensajería (SMTP, Resend, SMS o similares). Durante el MVP únicamente se genera el HTML del comprobante digital.
- Portal público de autoservicio para clientes finales.
- Venta de alimentos y bebidas.
- Generación automática o recurrente de funciones (plantillas de horario).
- Historial de cliente tipo CRM.
- Múltiples tipos de asiento por sala (general, VIP, discapacitados).
- Gestión de contingencias operativas (por ejemplo, reasignación de asistentes a otra sala por desperfecto técnico).

---

## 3. Actores

| Actor             | Descripción                                                                                                             | Acceso al sistema                  |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| **Administrador** | Configura películas, salas y funciones. Consulta reportes de ocupación.                                                 | Sí, con rol `admin`                |
| **Taquillero**    | Consulta disponibilidad, crea reservas a nombre de un cliente, cambia estados de reserva, consulta reporte de taquilla. | Sí, con rol `taquillero`           |
| **Cliente final** | Solicita la reserva de forma presencial o telefónica. Sus datos se registran en la reserva.                             | No tiene acceso directo al sistema |

---

## 4. Supuestos

| ID   | Supuesto                                                                                                                                                                                                                                 |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S-01 | Se asume que el sistema será utilizado por personal interno (administración y taquilla), debido a que el enunciado lo describe como un "módulo interno" y hace referencia explícita al "área de taquilla".                               |
| S-02 | Se asume que el cliente final no requiere cuenta ni autenticación propia en el sistema.                                                                                                                                                  |
| S-03 | Se asume que no hay procesamiento de pagos ni facturación dentro de este sistema, ya que el enunciado no lo menciona.                                                                                                                    |
| S-04 | Se asume que la distribución de asientos de una sala es fija una vez creada, y no se modifica si la sala ya tiene funciones programadas asociadas.                                                                                       |
| S-05 | Se asume un único tipo de asiento por sala, sin categorías diferenciadas (general, VIP, etc.).                                                                                                                                           |
| S-06 | Se asume que las funciones se crean de forma manual, una por una, sin recurrencia automática de horarios.                                                                                                                                |
| S-07 | Se asume que se puede reservar para cualquier función futura ya programada, no solo las del día en curso.                                                                                                                                |
| S-08 | Se asume que toda reserva nace en estado `Reservada` con una ventana de tiempo límite antes de expirar automáticamente si no se confirma.                                                                                                |
| S-09 | Se asume que no se distingue una razón o penalidad distinta entre cancelar desde `Reservada` versus desde `Confirmada`.                                                                                                                  |
| S-10 | Se asume que puede haber múltiples taquilleros operando simultáneamente sobre la misma función.                                                                                                                                          |
| S-11 | Se asume que las transiciones `Reservada → Confirmada` y `Confirmada → Utilizada` son realizadas manualmente por personal del cine, ya que el procesamiento de pagos y el control físico de ingreso están fuera del alcance del sistema. |
| S-12 | Se asume que el comprobante digital (Ticket) representa el derecho de ingreso asociado a un asiento reservado, y que el código QR mostrado es una representación visual del código del ticket, generada dinámicamente en el frontend.    |

---

## 5. Reglas de negocio

### 5.1 Reglas explícitas

Vienen literalmente del enunciado:

1. Una función corresponde a una película, en una sala, a una fecha y hora determinada.
2. Un asiento no puede reservarse dos veces para la misma función.
3. No se puede reservar para una función que ya inició.
4. No se pueden reservar más asientos de los que tiene la sala.
5. Estados de la reserva: `Reservada` → `Confirmada` → `Utilizada`. También puede `Cancelarse` o `Expirar`.
6. El reporte de taquilla debe mostrar: película, sala, horario, asientos ocupados, asientos disponibles, y el estado de cada reserva.

### 5.2 Reglas inferidas

Consecuencias casi inevitables del dominio, sin alternativa razonable:

1. **No pueden solaparse dos funciones en la misma sala.**
2. **Un asiento pertenece a una única sala**, y una reserva pertenece a una única función.
3. **Solo los asientos de reservas en estado activo** (`Reservada`, `Confirmada`, `Utilizada`) cuentan como ocupados. Al transicionar una reserva a `Cancelada` o `Expirada`, sus asientos dejan de contar como ocupados de forma automática, como consecuencia directa de esta regla — no requiere una acción separada de "liberación".
4. **No toda transición de estado es válida:**

   | De           | A            | Condición                                                        |
   | ------------ | ------------ | ---------------------------------------------------------------- |
   | —            | `Reservada`  | Asientos libres, función no iniciada, no excede aforo de la sala |
   | `Reservada`  | `Confirmada` | —                                                                |
   | `Reservada`  | `Cancelada`  | Función no iniciada                                              |
   | `Reservada`  | `Expirada`   | Venció el tiempo límite sin confirmarse                          |
   | `Confirmada` | `Utilizada`  | Una vez se utilize el ticket                                     |
   | `Confirmada` | `Cancelada`  | Función no iniciada                                              |

   Cualquier transición no listada se considera inválida. El enunciado no define qué ocurre con una reserva `Confirmada` cuyo cliente no se presenta (ver sección 9); el tratamiento adoptado para esta prueba técnica se documenta en la bitácora de decisiones.

5. **Cada asiento confirmado genera un único Ticket asociado permanentemente al asiento reservado.**
6. **El Ticket no posee un ciclo de vida propio**; su validez depende del estado de la Reserva a la que pertenece.

---

## 6. Requerimientos

### 6.1 Funcionales

| ID    | Descripción                                                                                                                                                                                            |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| RF-01 | El sistema permite disponer de un catálogo mínimo de películas, salas y funciones sobre el cual operar reservas.                                                                                       |
| RF-02 | El administrador puede crear funciones (película + sala + fecha + hora), validando que no se solape con otra función en la misma sala.                                                                 |
| RF-03 | El taquillero puede listar funciones junto con su disponibilidad de asientos (ocupados/libres).                                                                                                        |
| RF-04 | El taquillero puede crear una reserva para una función, seleccionando uno o más asientos libres, a nombre de un cliente.                                                                               |
| RF-05 | El sistema impide reservar o cancelar para una función que ya inició. El criterio exacto de corte (inicio de función vs. inicio de proyección) queda sujeto a definición del cliente (ver pregunta 6). |
| RF-06 | El sistema impide reservar más asientos de los que la sala tiene disponibles.                                                                                                                          |
| RF-07 | El sistema impide que un mismo asiento se reserve dos veces para la misma función.                                                                                                                     |
| RF-08 | El taquillero puede cambiar el estado de una reserva, respetando únicamente las transiciones válidas de la sección 5.2.                                                                                |
| RF-09 | El sistema expira automáticamente una reserva `Reservada` cuyo tiempo límite venció.                                                                                                                   |
| RF-10 | El sistema genera un reporte de taquilla con: película, sala, horario, asientos ocupados, asientos disponibles, y estado de cada reserva.                                                              |
| RF-11 | El sistema puede generar un Ticket por cada asiento confirmado.                                                                                                                                        |
| RF-12 | El sistema permite visualizar el comprobante digital del Ticket.                                                                                                                                       |
| RF-13 | El taquillero puede consultar el detalle de ocupación asiento por asiento de una función específica, viendo cuáles están libres u ocupados y, si están ocupados, a qué reserva pertenecen.            |

### 6.2 No funcionales

| ID     | Descripción                                                                                                                               |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| RNF-01 | **Integridad de datos**: un asiento nunca debe quedar doblemente reservado para una misma función, incluso bajo operaciones concurrentes. |
| RNF-02 | **Concurrencia**: soportar múltiples taquilleros operando simultáneamente sobre la misma función sin inconsistencias.                     |
| RNF-03 | **Seguridad**: acceso autenticado por rol; validación y sanitización de entradas; prevención de inyección SQL.                            |
| RNF-04 | **Manejo de errores**: errores de negocio comunicados de forma clara y controlada.                                                        |
| RNF-05 | **Auditoría**: cambios de estado registrados (quién, cuándo, de qué estado a cuál).                                                       |

### 6.3 Priorización

| Funcionalidad                                     | Prioridad         | Justificación                                                                                                                 |
| ------------------------------------------------- | ----------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Crear reserva                                     | Obligatoria       | Requisito principal del ejercicio.                                                                                            |
| Listar funciones y disponibilidad                 | Obligatoria       | Solicitado explícitamente.                                                                                                    |
| Cambiar estado de reserva                         | Obligatoria       | Solicitado explícitamente.                                                                                                    |
| Reporte de taquilla                               | Obligatoria       | Solicitado explícitamente.                                                                                                    |
| Integridad de datos y concurrencia                | Obligatoria       | Mayor riesgo técnico del sistema.                                                                                             |
| Gestionar catálogo necesario para crear funciones | Obligatoria       | Dependencia técnica del requisito principal.                                                                                  |
| CRUD completo del catálogo                        | Deseable          | No es el foco del ejercicio, pero se implementó igual (rooms, movies, movie-functions).                                      |
| Validación y sanitización básica                  | Obligatoria       | Higiene mínima no negociable.                                                                                                 |
| Auditoría de cambios de estado                    | Deseable          | No bloquea el mínimo funcional.                                                                                               |
| Actualización en tiempo real en pantalla          | Deseable          | Mejora de experiencia, no de correctitud.                                                                                     |
| Ticket (comprobante digital)                      | Extensión del MVP | No forma parte del mínimo funcional pedido, pero se incorpora como valor agregado natural una vez que la reserva se confirma. |
| Generación automática/recurrente de funciones     | Fuera de alcance  | No mencionado en el enunciado.                                                                                                |
| Reasignación de sala por contingencia             | Fuera de alcance  | No mencionado en el enunciado; mejora futura.                                                                                 |

---

## 7. Preguntas para el cliente

1. Se interpretó el sistema como una herramienta exclusivamente operada por personal de taquilla, dado que el enunciado lo describe como "módulo interno". ¿Es correcta esta interpretación para el alcance actual?
2. ¿Cuánto tiempo debe durar el periodo en que una reserva permanece `Reservada` antes de expirar automáticamente?
3. ¿Cuál debe ser el comportamiento de una reserva `Confirmada` cuando el cliente no se presenta a la función (no-show)?
4. ¿Se permite modificar una reserva ya creada (cambiar asientos o cantidad), o solo cancelarla y crear una nueva?
5. ¿Existe un límite máximo de asientos por reserva?
6. ¿El corte para dejar de aceptar reservas o cancelaciones ocurre al inicio de la función o al inicio de la proyección de la película (por ejemplo, después de los anuncios)?
7. ¿Debe existir un tiempo mínimo de limpieza o preparación entre el fin de una función y el inicio de la siguiente en la misma sala? ¿Cuánto?
8. ¿Se requiere registrar qué taquillero específico creó o modificó cada reserva?
9. ¿La verificación de ingreso será realizada por el mismo rol de taquillero, o existirá un rol independiente para el personal de acceso a sala?

---

## 8. Casos de uso principales

### CU-01 — Crear reserva

**Actor:** Taquillero
**Precondiciones:** función existe y no ha iniciado; asientos disponibles; no excede aforo.
**Flujo principal:**

1. Buscar la función deseada.
2. Consultar disponibilidad de asientos.
3. Seleccionar asientos.
4. Registrar datos mínimos del cliente.
5. Confirmar la creación de la reserva.
   **Postcondiciones:** reserva creada en `Reservada`; asientos marcados como ocupados.

### CU-02 — Cambiar estado de una reserva

**Actor:** Taquillero
**Precondiciones:** reserva existe; transición es válida.
**Flujo principal:**

1. Buscar la reserva.
2. Seleccionar nuevo estado.
3. Sistema valida transición y condición (función no iniciada, si aplica).
4. Se actualiza el estado.
   **Postcondiciones:** nuevo estado aplicado. Si el nuevo estado es `Cancelada` o `Expirada`, los asientos dejan de contar como ocupados de forma automática (regla 5.2.3), sin requerir un paso adicional.

### CU-03 — Consultar disponibilidad de funciones

**Actor:** Taquillero
**Flujo principal:** buscar funciones; el sistema muestra ocupados/disponibles por función. Opcionalmente, para una función puntual, el taquillero puede ver el detalle asiento por asiento (libre/ocupado y su reserva asociada).

### CU-04 — Consultar reporte de taquilla

**Actor:** Taquillero o Administrador
**Flujo principal:** seleccionar función; el sistema muestra película, sala, horario, ocupados, disponibles y estado de cada reserva.

### CU-05 — Generar comprobante

**Actor:** Taquillero
**Precondiciones:** la reserva se encuentra en estado `Confirmada`.
**Flujo principal:**

1. La reserva cambia a `Confirmada`.
2. El sistema genera un Ticket por cada asiento de la reserva.
3. Se muestra el comprobante digital (HTML).
   **Postcondiciones:** cada asiento confirmado posee un Ticket único asociado.

---

## 9. Riesgos e incertidumbres

| Incertidumbre de negocio                                                                                                               | Impacto potencial                                                                                                                     |
| -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| No está definido el tiempo exacto del periodo de espera antes de que una reserva `Reservada` expire.                                   | Se resuelve con un valor de ejemplo, documentado en la bitácora de decisiones.                                                        |
| El comportamiento de una reserva `Confirmada` cuando el cliente no se presenta a la función no está definido por el enunciado.         | Distintos cines resuelven esto de forma distinta; el tratamiento adoptado para esta prueba se documenta en la bitácora de decisiones. |
| No está definido si el corte para reservar/cancelar es el inicio de la función o el inicio de la proyección (después de anuncios).     | Afecta el cálculo exacto del límite de tiempo en la validación.                                                                       |
| No está definido si se permite modificar una reserva existente en lugar de solo cancelarla.                                            | Afectaría el modelo de transiciones y el diseño de la operación de edición.                                                           |
| No está definido si existe un límite máximo de asientos por reserva.                                                                   | Podría requerir una validación adicional no contemplada.                                                                              |
| No está definido si se requiere un tiempo mínimo de limpieza entre funciones consecutivas en la misma sala.                            | Afectaría la validación de solapamiento de funciones (regla 5.2.1).                                                                   |
| No está definido si el ingreso de los asistentes ocurre de forma individual (por asiento) o siempre como grupo (por reserva completa). | En el MVP el estado de uso se maneja a nivel de Reserva; una evolución futura podría manejarse a nivel de Ticket individual.          |

---

## 10. Criterios de aceptación

- No permite reservar o cancelar para una función que ya inició.
- No permite reservar un asiento ya ocupado para la misma función.
- No permite reservar más asientos de los disponibles en la sala.
- Solo permite transiciones de estado válidas; cualquier otra debe rechazarse.
- El reporte de taquilla muestra ocupados, disponibles y el estado de cada reserva, por función.
- Una reserva `Reservada` vencida se refleja como `Expirada` al consultarse.
- Cada asiento confirmado genera un Ticket con comprobante digital visualizable.

---

## 11. Glosario

| Término            | Definición                                                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| **Función**        | Proyección específica de una película, en una sala, en una fecha y hora concretas.                                              |
| **Reserva activa** | Reserva en `Reservada`, `Confirmada` o `Utilizada`.                                                                             |
| **Aforo**          | Capacidad total de asientos de una sala.                                                                                        |
| **No-show**        | Cliente con reserva `Confirmada` que no se presenta a la función.                                                               |
| **Ticket**         | Comprobante digital asociado a un asiento reservado. Contiene un código único utilizado para representar el derecho de ingreso. |

---

_Este documento se enfoca en el entendimiento del negocio. El razonamiento técnico detrás de cada mecanismo (incluyendo el tratamiento adoptado para no-show, el margen de corte de reservas/cancelaciones, y el modelo de concurrencia para evitar doble reserva de asientos) se documenta en la bitácora de decisiones, y su traducción a esquema de datos en el diseño de base de datos._
