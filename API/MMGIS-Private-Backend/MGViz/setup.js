const MGVizRouter = require("./routes/mgviz");

const swaggerMGViz = require("./swaggers/swaggerMGViz.json");

let setup = {
  //Once the app initializes
  onceInit: s => {
    s.app.use(
      "/API/MGViz",
      s.ensureUser(),
      s.checkHeadersCodeInjection,
      s.setContentType,
      MGVizRouter
    );

    s.app.use(
      "/api/docs/MGViz",
      s.swaggerUi.serve,
      s.useSwaggerSchema(swaggerMGViz)
    );
  },
  //Once the server starts
  onceStarted: s => {},
  //Once all tables sync
  onceSynced: s => {}
};

module.exports = setup;