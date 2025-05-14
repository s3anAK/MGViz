const express = require("express");
const router = express.Router();
const { sequelize } = require("../../../connection");
const logger = require("../../../logger");

const isValidString = (str) => {
  return str && typeof str === "string" && /^[a-zA-Z0-9_\-\.]+$/.test(str);
};

router.get("/coseismic", function (req, res, next) {
  coseismic(req, res, next, "get");
});

router.get("/detections", function (req, res, next) {
  detections(req, res, next, "get");
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
            coseismic_id: params.id,
          },
        }
      )
      .then(([sites]) => {
        res.send({ sites });
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
  } else {
    //Get list of coseismics
    sequelize
      .query(
        "SELECT id, concat_ws(' -- ', concat_ws(' -- ', time_utc, magnitude), location) as time_utc" +
          " " +
          "FROM coseismic" +
          " " +
          "ORDER BY time_utc DESC"
      )
      .then(([coseismics]) => {
        res.send({ coseismics });
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

function detections(req, res, next, type) {
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

  if (isISODateString(params.startdate) && isISODateString(params.enddate)
    && isValidString(params.mode) && isValidString(params.model)) {
    sequelize
      .query(
        "SELECT json_build_object('type', 'FeatureCollection', 'features', json_agg(json_build_object('type', 'Feature', 'geometry', ST_AsGeoJSON(geom)::json, 'properties', jsonb_strip_nulls(to_jsonb(detection_site) - 'geometry')))) FROM (SELECT site.id, model.name, model.mode, detection_id, detection.label, eventtype, startdate, enddate, ST_GeomFROMText('POINT(' || cast(x as text)|| ' ' || cast(y as text) || ')', 4326) as geom FROM public.detection, site, model WHERE detection.site_id = site.id and probability is not null AND detection.model_id = model.id AND model.mode = $mode AND model.name = $model AND (startdate, enddate) OVERLAPS ($startdate, $enddate)) as detection_site;",
        {
          bind: {
            startdate: params.startdate,
            enddate: params.enddate,
            mode: params.mode,
            model: params.model,
          },
        }
      )
      .then(([detections]) => {
        res.send(detections[0]["json_build_object"]);
      })
      .catch((err) => {
        logger(
          "error",
          "SQL error while acquiring detections.",
          req.originalUrl,
          req,
          err
        );
        res.send({
          status: "failure",
          message: "SQL error while acquiring detections.",
          body: {},
        });
      });
  } else if (isISODateString(params.startdate) && isISODateString(params.enddate)) {
    sequelize
      .query(
        "SELECT json_build_object('type', 'FeatureCollection', 'features', json_agg(json_build_object('type', 'Feature', 'geometry', ST_AsGeoJSON(geom)::json, 'properties', jsonb_strip_nulls(to_jsonb(detection_site) - 'geometry')))) FROM (SELECT site.id, model.name, model.mode, detection_id, detection.label, eventtype, startdate, enddate, ST_GeomFROMText('POINT(' || cast(x as text)|| ' ' || cast(y as text) || ')', 4326) as geom FROM public.detection, site, model WHERE detection.site_id = site.id and probability is not null AND detection.model_id = model.id AND (startdate, enddate) OVERLAPS ($startdate, $enddate)) as detection_site;",
        {
          bind: {
            startdate: params.startdate,
            enddate: params.enddate,
          },
        }
      )
      .then(([detections]) => {
        res.send(detections[0]["json_build_object"]);
      })
      .catch((err) => {
        logger(
          "error",
          "SQL error while acquiring detections.",
          req.originalUrl,
          req,
          err
        );
        res.send({
          status: "failure",
          message: "SQL error while acquiring detections.",
          body: {},
        });
      });
  } else {
    sequelize
      .query(
        "SELECT json_build_object('type', 'FeatureCollection', 'features', json_agg(json_build_object('type', 'Feature', 'geometry', ST_AsGeoJSON(geom)::json, 'properties', jsonb_strip_nulls(to_jsonb(detection_site) - 'geometry')))) FROM (SELECT site.id, model.name, model.mode, detection_id, detection.label, eventtype, startdate, enddate, ST_GeomFROMText('POINT(' || cast(x as text)|| ' ' || cast(y as text) || ')', 4326) as geom FROM public.detection, site, model WHERE detection.site_id = site.id and probability is not null AND detection.model_id = model.id) as detection_site;"
      )
      .then(([detections]) => {
        res.send(detections[0]["json_build_object"]);
      })
      .catch((err) => {
        logger(
          "error",
          "SQL error while acquiring detections.",
          req.originalUrl,
          req,
          err
        );
        res.send({
          status: "failure",
          message: "SQL error while acquiring detections.",
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
      res.send(earthquakes[0]["json_build_object"]);
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

function isISODateString(dateString) {
  const date = new Date(dateString);
  return !isNaN(date.getTime()) && dateString === date.toISOString();
}

module.exports = router;
