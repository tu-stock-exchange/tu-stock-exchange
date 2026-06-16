# Build stage
FROM node:20 as build-stage

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Accept the build argument and expose it to Vite
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build the Vue app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx config for SPA routing
#COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
#EXPOSE 80

# Start nginx
#CMD ["nginx", "-g", "daemon off;"]


FROM nginx:alpine
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Use environment variable PORT (set by Cloud Run)
ENV PORT 8080
EXPOSE ${PORT}
CMD sed -i "s/listen 80;/listen ${PORT};/g" /etc/nginx/conf.d/default.conf && nginx -g "daemon off;"