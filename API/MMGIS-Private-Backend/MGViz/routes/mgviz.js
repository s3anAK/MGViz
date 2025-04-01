const express = require("express");
const router = express.Router();
const { sequelize } = require("../../../connection");
const logger = require("../../../logger");


router.get("/coseismic", function (req, res, next) {
  coseismic(req, res, next, "get");
});

router.get("/earthquakes", function (req, res, next) {
  earthquakes(req, res, next, "get");
});


function coseismic(req, res, next, type) {
  //Have it accept either post or get
  let params = null;
  if (type === "get") params = req.query;
  else if (type === "post") params = req.body;
  else {
    res.send({
      status: "failure",
      message: "Unexpected HTTP method: " + type,
      body: {},
    });
    return;
  }

  if (params.id && Number.isInteger(parseInt(params?.id))) {
    //Get list of sites associated with coseismic id
    sequelize
    .query(
      "SELECT site_id, x, y, neu, time_utc" +
        " " +
        "FROM site_coseismic, coseismic, site" +
        " " +
        "WHERE site_coseismic.coseismic_id = $site_coseismic_id" +
        " " +
        "AND coseismic.id = $coseismic_id" +
        " " + 
        "AND site.id = site_id" +
        " " + 
        "ORDER BY site_id ASC",
        {
          bind: {
              site_coseismic_id: params.id,
              coseismic_id: params.id
          }
        }
    )
    .then(([sites]) => {
      res.send({sites})
    })
    .catch((err) => {
      logger(
        "error",
        "SQL error while acquiring coseismic sites.",
        req.originalUrl,
        req,
        err
      );
      res.send({
        status: "failure",
        message: "SQL error while acquiring coseismic sites.",
        body: {},
      });
    });    
  }
  else {
    //Get list of coseismics
    sequelize
      .query(
        "SELECT id, concat_ws(' -- ', time_utc, location) as time_utc" +
          " " +
          "FROM coseismic" +
          " " +
          "ORDER BY time_utc DESC"
      )
      .then(([coseismics]) => {
        res.send({coseismics})
      })
      .catch((err) => {
        logger(
          "error",
          "SQL error while acquiring coseismics.",
          req.originalUrl,
          req,
          err
        );
        res.send({
          status: "failure",
          message: "SQL error while acquiring coseismics.",
          body: {},
        });
      });
  }
}

function earthquakes(req, res, next, type) {
  //Have it accept either post or get
  let params = null;
  if (type === "get") params = req.query;
  else if (type === "post") params = req.body;
  else {
    res.send({
      status: "failure",
      message: "Unexpected HTTP method: " + type,
      body: {},
    });
    return;
  }

  sequelize
    .query(
      "SELECT json_build_object(" +
      "'type', 'FeatureCollection'," +
      "'features', json_agg(" +
          "json_build_object(" +
              "'type', 'Feature'," +
              "'geometry', ST_AsGeoJSON(geom)::json," +
              "'properties', jsonb_strip_nulls(to_jsonb(coseismic) - 'geometry')" +
          ")" +
        ")" +
      ")" +
      "FROM coseismic"
    )
    .then(([earthquakes]) => {
      res.send(earthquakes[0]['json_build_object'])
    })
    .catch((err) => {
      logger(
        "error",
        "SQL error while acquiring earthquakes.",
        req.originalUrl,
        req,
        err
      );
      res.send({
        status: "failure",
        message: "SQL error while acquiring earthquakes.",
        body: {},
      });
    });
}


module.exports = router;
