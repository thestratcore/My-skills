FROM node:24-alpine
ENV NODE_ENV=production
WORKDIR /app
COPY server.js worker.js ./
COPY scripts ./scripts
RUN mkdir /data && chown node:node /data
USER node
EXPOSE 3000
HEALTHCHECK --interval=2s --timeout=3s --start-period=2s --retries=10 \
  CMD wget -q --spider http://127.0.0.1:3000/healthz || exit 1
CMD ["node", "server.js"]
