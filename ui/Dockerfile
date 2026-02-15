# Base Image: Node.js 20 (Alpine)
FROM node:20-alpine

# Working Directory
WORKDIR /app

# Install dependencies (cache mount for speed)
COPY package.json package-lock.json ./
RUN npm ci

# Copy Source
COPY . .

# Build Next.js App
RUN npm run build

# Expose Port 3000
EXPOSE 3000

# Start Command
CMD ["npm", "start"]
