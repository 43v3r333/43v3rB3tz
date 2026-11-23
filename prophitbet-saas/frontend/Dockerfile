FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund --fetch-retries=3

COPY . .

# Verify production compile (dev server does not require this at runtime)
RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
