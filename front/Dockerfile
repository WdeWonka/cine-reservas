# --- Etapa 1: build ---
FROM node:22-alpine AS build

WORKDIR /app

RUN npm install -g pnpm

ENV PNPM_CONFIG_STRICT_DEP_BUILDS=false

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --config.strict-dep-builds=false

COPY . .
RUN pnpm exec ng build --configuration production

# --- Etapa 2: runtime ---
FROM nginx:alpine

# El proyecto se llama "front" (ver angular.json → projects.front), y usa
# el builder moderno de Angular (@angular/build:application, esbuild), que
# genera la salida en dist/<proyecto>/browser/, no directo en dist/<proyecto>/.
COPY --from=build /app/dist/front/browser/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
