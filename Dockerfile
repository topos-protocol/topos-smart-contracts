FROM node:lts-slim as base
WORKDIR /usr/src/app
COPY package*.json .
RUN npm install
COPY . .

FROM base as test
RUN npm run test

FROM base as format
RUN npm run format

FROM base as lint
RUN npm run lint

FROM base as build
# TMP
# RUN npm run build
RUN while [ ! -d ./artifacts ]; do npm run build; done
