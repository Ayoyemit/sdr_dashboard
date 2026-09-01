FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
ENV NODE_ENV=production

RUN npm run build

EXPOSE 3000

CMD ["sh", "-c", "npx next start -p ${PORT:-3000}"]
