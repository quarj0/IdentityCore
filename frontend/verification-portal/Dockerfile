FROM node:22-alpine AS base
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
RUN corepack enable

FROM base AS build
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY packages ./packages
COPY verification-portal ./verification-portal
RUN pnpm install --frozen-lockfile
RUN pnpm --filter verification-portal build

FROM node:22-alpine AS runtime
ENV NODE_ENV=production
ENV PORT=3002
ENV HOSTNAME=0.0.0.0
WORKDIR /app
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=build --chown=nextjs:nodejs /app/verification-portal/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/verification-portal/.next/static ./verification-portal/.next/static
COPY --from=build --chown=nextjs:nodejs /app/verification-portal/public ./verification-portal/public
USER nextjs
EXPOSE 3002
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3002/api/health').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]
CMD ["node", "verification-portal/server.js"]
