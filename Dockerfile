FROM node:lts-slim as base
WORKDIR /usr/src/app
COPY package*.json .
RUN npm install
COPY . .

FROM base as test
RUN npm run test

FROM base as lint
RUN npm run lint

FROM base as build
RUN npm run build
