# frontend/Dockerfile

# Build stage
FROM node:18-alpine as build

WORKDIR /app

COPY package.json ./
# Use package-lock.json if it exists, for reproducible builds
COPY package-lock.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine

COPY --from=build /app/build /usr/share/nginx/html

# Copy the nginx config
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
