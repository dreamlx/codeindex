const express = require('express');
const { Router } = require('./router');

class App {
  constructor(port) {
    this.port = port;
    this.router = new Router();
    this.app = express();
  }

  get(path, handler) {
    this.router.get(path, handler);
  }

  post(path, handler) {
    this.router.post(path, handler);
  }

  listen() {
    this.app.listen(this.port, () => {
      console.log(`Server running on port ${this.port}`);
    });
  }
}

function createApp(port) {
  const app = new App(port);
  app.get('/', (req, res) => res.send('Hello'));
  return app;
}

module.exports = { App, createApp };
