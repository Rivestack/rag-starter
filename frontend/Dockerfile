FROM node:20-slim AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-slim

WORKDIR /app

COPY --from=build /app/.output .output

ENV PORT=3000
EXPOSE ${PORT}

CMD ["node", ".output/server/index.mjs"]
