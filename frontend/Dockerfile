FROM node:22-bookworm-slim

WORKDIR /workspace/frontend

ENV NODE_OPTIONS=--dns-result-order=ipv4first

COPY package*.json ./

RUN npm config set registry https://registry.npmmirror.com \
    && npm config set fetch-retries 10 \
    && npm config set fetch-retry-factor 2 \
    && npm config set fetch-retry-mintimeout 30000 \
    && npm config set fetch-retry-maxtimeout 180000 \
    && npm config set fetch-timeout 900000 \
    && if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]