FROM node:lts-slim as base

WORKDIR /usr/src/app

RUN apt update && apt install -y python3 python3-pip
    
RUN pip3 install eth-brownie

COPY package.json yarn.lock ./

RUN yarn install

COPY . .

FROM base as test

RUN yarn test

FROM base as lint

RUN yarn lint

FROM base as build

RUN brownie compile
