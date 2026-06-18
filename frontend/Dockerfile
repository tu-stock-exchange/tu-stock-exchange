# Build stage
FROM node:20 as build-stage

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# Accept the build argument and expose it to Vite
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx config for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Use environment variable PORT (set by Cloud Run)
ENV PORT 8080
EXPOSE ${PORT}
CMD sed -i "s/listen 80;/listen ${PORT};/g" /etc/nginx/conf.d/default.conf && nginx -g "daemon off;"