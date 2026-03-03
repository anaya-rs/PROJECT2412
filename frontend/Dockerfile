FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --only=production

EXPOSE 80

CMD ["npm", "run", "preview"]
