export const GUATEMALA_TIMEZONE = 'America/Guatemala';

/**
 * La API devuelve todos los datetime como naive-UTC (sin sufijo de zona,
 * ej. "2026-07-19T19:00:00"). Si se le pasa tal cual a `new Date(...)`,
 * el motor JS lo interpreta como hora LOCAL del browser, no UTC. Forzamos
 * el sufijo "Z" antes de parsear.
 */
export function parseUtcIso(value: string): Date {
  const hasTimezone = /[zZ]|[+-]\d{2}:\d{2}$/.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
}

/**
 * Offset real (en minutos) de una zona horaria IANA respecto a UTC, en un
 * instante dado. Se deriva de Intl.DateTimeFormat en vez de un número
 * hardcodeado — Guatemala no tiene horario de verano, pero preferimos no
 * asumirlo a mano igual.
 */
export function getUtcOffsetMinutes(timeZone: string, at: Date = new Date()): number {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone,
    hourCycle: 'h23',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
    .formatToParts(at)
    .reduce<Record<string, string>>((acc, part) => ({ ...acc, [part.type]: part.value }), {});

  const asUtc = Date.UTC(
    Number(parts['year']),
    Number(parts['month']) - 1,
    Number(parts['day']),
    Number(parts['hour']),
    Number(parts['minute']),
    Number(parts['second']),
  );

  return (asUtc - at.getTime()) / 60_000;
}

/**
 * Convierte un "wall clock" (año/mes/día/hora/minuto tal cual los tipeó
 * el usuario, pensados como hora de Guatemala) al ISO naive-UTC que
 * espera la API. No asume que el browser está en huso horario Guatemala.
 */
export function guatemalaWallClockToUtcIso(wallClock: Date): string {
  const offsetMinutes = getUtcOffsetMinutes(GUATEMALA_TIMEZONE);
  const asIfUtcMillis = Date.UTC(
    wallClock.getFullYear(),
    wallClock.getMonth(),
    wallClock.getDate(),
    wallClock.getHours(),
    wallClock.getMinutes(),
    0,
  );
  return new Date(asIfUtcMillis - offsetMinutes * 60_000).toISOString().replace('Z', '');
}

/**
 * Rango UTC [inicio, fin) correspondiente a un día calendario completo en
 * Guatemala (00:00 a 24:00 hora Guatemala). Como Guatemala es UTC-6, ese
 * rango NO coincide con un día calendario UTC — por eso este cálculo es
 * el filtro autoritativo para "funciones de hoy en Guatemala", no el
 * `?date=` (naive-UTC) del backend, que como mucho sirve de acotador.
 */
export function guatemalaDayUtcRange(dateIso: string): { start: Date; end: Date } {
  const [year, month, day] = dateIso.split('-').map(Number);
  const offsetMinutes = getUtcOffsetMinutes(GUATEMALA_TIMEZONE);
  const startUtcMillis = Date.UTC(year, month - 1, day, 0, 0, 0) - offsetMinutes * 60_000;
  return {
    start: new Date(startUtcMillis),
    end: new Date(startUtcMillis + 24 * 60 * 60 * 1000),
  };
}

/** "YYYY-MM-DD" de hoy, en hora de Guatemala (no la del browser). */
export function todayInGuatemala(): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: GUATEMALA_TIMEZONE }).format(new Date());
}
