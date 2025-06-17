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

router.get("/detection", function (req, res, next) {
  detection(req, res, next, "get");
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

function detection(req, res, next, type) {
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
      "SELECT * FROM detection, model " + 
	    "WHERE detection.model_id = model.id " +
	    "AND mode = $mode " +
	    "AND name = $model " +
	    "AND site_id = $site " +
      "ORDER BY detection.id ASC",
      {
        bind: {
          mode: params.mode,
          model: params.model,
          site: params.site,
        },
      }
    )
    .then(([detection]) => {
      result = {}
      metadata = {}
      detections = []

      if (detection.length > 0) {
        metadata['label'] = detection[0]['label']
        metadata['stationid'] = detection[0]['site_id']
        metadata['eventtype'] = detection[0]['eventtype']
        metadata['modelid'] = detection[0]['model_id']

        for (let i = 0; i < detection.length; i++) {
          if (params.mode === "tropospheric") {
            formattedStart = (new Date(detection[i]['startdate'])).getTime()
            formattedEnd = (new Date(detection[i]['enddate'])).getTime()
          } else {
            formattedStart = dateToDecimalDate(new Date(detection[i]['startdate']))
            formattedEnd = dateToDecimalDate(new Date(detection[i]['enddate']))
          }
          d = {
            detection_id: detection[i]['detection_id'],
            startdate: formattedStart,
            enddate: formattedEnd,
            probability: detection[i]['probability']
          }
          detections[i] = d
        }
        result['metadata'] =  metadata
        result['detections'] = detections
      }
      res.send(result);
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
        "SELECT json_build_object('type', 'FeatureCollection', 'features', json_agg(json_build_object('type', 'Feature', 'geometry', ST_AsGeoJSON(geom)::json, 'properties', jsonb_strip_nulls(to_jsonb(detection_site) - 'geometry')))) FROM (SELECT site.id, model.name, model.mode, detection_id, detection.label, eventtype, probability, startdate, enddate, ST_GeomFROMText('POINT(' || cast(x as text)|| ' ' || cast(y as text) || ')', 4326) as geom FROM public.detection, site, model WHERE detection.site_id = site.id and probability is not null AND detection.model_id = model.id AND model.mode = $mode AND model.name = $model AND (startdate, enddate) OVERLAPS ($startdate, $enddate)) as detection_site;",
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
        "SELECT json_build_object('type', 'FeatureCollection', 'features', json_agg(json_build_object('type', 'Feature', 'geometry', ST_AsGeoJSON(geom)::json, 'properties', jsonb_strip_nulls(to_jsonb(detection_site) - 'geometry')))) FROM (SELECT site.id, model.name, model.mode, detection_id, detection.label, eventtype, probability, startdate, enddate, ST_GeomFROMText('POINT(' || cast(x as text)|| ' ' || cast(y as text) || ')', 4326) as geom FROM public.detection, site, model WHERE detection.site_id = site.id and probability is not null AND detection.model_id = model.id AND (startdate, enddate) OVERLAPS ($startdate, $enddate)) as detection_site;",
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
        "SELECT json_build_object('type', 'FeatureCollection', 'features', json_agg(json_build_object('type', 'Feature', 'geometry', ST_AsGeoJSON(geom)::json, 'properties', jsonb_strip_nulls(to_jsonb(detection_site) - 'geometry')))) FROM (SELECT site.id, model.name, model.mode, detection_id, detection.label, eventtype, probability, startdate, enddate, ST_GeomFROMText('POINT(' || cast(x as text)|| ' ' || cast(y as text) || ')', 4326) as geom FROM public.detection, site, model WHERE detection.site_id = site.id and probability is not null AND detection.model_id = model.id) as detection_site;"
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

function dateToDecimalDate(date) {
    const year = date.getFullYear();
    const start = new Date(year, 0, 1);
    const end = new Date(year + 1, 0, 1);

    // Calculate the fraction of the year that has passed
    const yearLength = end - start;
    const elapsed = date - start;

    // Decimal date = year + fraction of year elapsed
    const decimalDate = year + (elapsed / yearLength);
    return Number(decimalDate.toFixed(4));
}

module.exports = router;
