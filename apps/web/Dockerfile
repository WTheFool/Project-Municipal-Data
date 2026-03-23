#web/Dockerfile
# Base image
FROM node:20

# Working directory
WORKDIR /web

# Copy package.json and lockfile first
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the source code (excluding node_modules due to .dockerignore)
COPY . .

# Expose dev server port
EXPOSE 5173

# Start dev server
CMD ["npm", "run", "dev", "--", "--host"]