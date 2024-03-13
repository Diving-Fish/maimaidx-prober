FROM node:16.20-alpine3.17

RUN npm install -g http-server

WORKDIR /app

COPY package*.json ./

RUN npm config set strict-ssl false

RUN npm install

COPY . .

RUN npm run build

EXPOSE 8080
CMD ["http-server", "dist"]