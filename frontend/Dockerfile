FROM node:22-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-alpine AS serve
RUN npm install -g serve

COPY --from=build /app/dist /usr/share/app
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
