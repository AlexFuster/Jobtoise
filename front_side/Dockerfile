FROM node:20.18.1-alpine

WORKDIR /app

COPY babel.config.js .
COPY jsconfig.json .
COPY vue.config.js .
COPY package.json .
COPY public public
COPY src src

RUN npm install

EXPOSE 8080

CMD ["npm","run","serve"]