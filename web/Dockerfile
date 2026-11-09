FROM node:22

WORKDIR /app

COPY package*.json ./

RUN npm ci \
    --no-audit \
    --no-fund \
    --fetch-retries=5 \
    --fetch-retry-mintimeout=20000 \
    --fetch-retry-maxtimeout=120000 \
    --maxsockets=1

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]