FROM node:22-alpine AS deps
WORKDIR /app/backend
COPY backend/package.json backend/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts && npm cache clean --force

FROM node:22-alpine
ENV NODE_ENV=production \
    PORT=3001 \
    HOST=0.0.0.0 \
    DATA_DIR=/data
WORKDIR /app/backend
COPY --from=deps /app/backend/node_modules ./node_modules
COPY backend/package.json ./
COPY backend/src ./src
COPY web/public /app/web/public
RUN mkdir -p /data && chown -R node:node /app /data
USER node
EXPOSE 3001
VOLUME ["/data"]
HEALTHCHECK --interval=15s --timeout=5s --retries=5 --start-period=10s \
  CMD node -e "fetch('http://127.0.0.1:3001/api/health').then(r=>r.json()).then(j=>{if(!j.ready)process.exit(1)}).catch(()=>process.exit(1))"
CMD ["node", "src/server.js"]
