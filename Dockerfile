FROM node:lts-slim as base

WORKDIR /usr/src/app

RUN apt update && apt install -y python3 python3-pip expect
    
RUN pip3 install eth-brownie

COPY package*.json .

RUN npm install

COPY . .

FROM base as test

RUN npm run test

FROM base as lint

RUN npm run lint

FROM base as build

RUN npm run build
