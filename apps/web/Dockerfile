FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci


FROM node:22-slim AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build


FROM node:22-slim AS runner
# node:22-slim already ships a non-root `node` user at uid 1000 — reuse it
# instead of creating a second one (useradd would collide on that uid).
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder --chown=node:node /app/.next/standalone ./
COPY --from=builder --chown=node:node /app/.next/static ./.next/static

USER node
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD node -e "fetch('http://localhost:3000/login').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

# Docker auto-sets HOSTNAME to the container's own id for every container,
# which shadows the standalone server's `process.env.HOSTNAME || '0.0.0.0'`
# fallback and binds it to that id instead of all interfaces — unreachable
# from sibling containers (Traefik included). A Dockerfile ENV can't be
# trusted to win that race, so force it right at exec time instead.
CMD ["/bin/sh", "-c", "HOSTNAME=0.0.0.0 exec node server.js"]
