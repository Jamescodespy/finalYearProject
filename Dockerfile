FROM node:16

# Create app directory
WORKDIR /usr/src/app
ENV DATABASE_HOST='http://172.17.0.1:1000/'

# Install app dependencies
# A wildcard is used to ensure both package.json AND package-lock.json are copied
# where available (npm@5+)
COPY package*.json ./

RUN npm install
# If you are building your code for production
# RUN npm ci --only=production

# Bundle app source
COPY . .

EXPOSE 3000
CMD [ "node", "src/index.js" ]
