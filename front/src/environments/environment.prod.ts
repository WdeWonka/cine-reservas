// Mismo shape que environment.ts. Hoy apunta al mismo host:puerto porque
// el docker-compose.yml actual publica la API en localhost:8000 también
// en el escenario "productivo" local (todo corre en el mismo host). Si
// algún día la API se sirve en otro dominio/subdominio real, actualizar
// apiUrl acá.
export const environment = {
  apiUrl: 'http://localhost:8000',
};
