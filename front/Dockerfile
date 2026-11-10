FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-alpine

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=4173

COPY server.js ./server.js
COPY --from=build /app/dist ./dist

EXPOSE 4173

CMD ["node", "server.js"]
