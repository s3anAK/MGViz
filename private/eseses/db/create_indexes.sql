-- Increase work memory for complex queries
SET work_mem = '256MB'; -- 4MB default

-- Model filtering
CREATE INDEX idx_model_mode_name ON public.model (mode, name);

-- Date range queries  
CREATE INDEX idx_detection_dates ON public.detection (startdate, enddate);

-- Window function optimization
CREATE INDEX idx_detection_site_enddate ON public.detection (site_id, enddate DESC);

-- Satisfy DISTINCT ON ordering without a sort
CREATE INDEX CONCURRENTLY idx_detection_site_enddate_desc
    ON public.detection (site_id, enddate DESC)
    INCLUDE (model_id, probability, startdate, enddate)
    WHERE probability IS NOT NULL;

-- Optimized detection query that covers all WHERE conditions in optimal order for index-only scans
CREATE INDEX CONCURRENTLY idx_detection_query_optimized ON public.detection 
(model_id, startdate, enddate, site_id, probability)
WHERE probability IS NOT NULL;

-- Partial index for recent data (2023+) - helps with recent data performance
CREATE INDEX CONCURRENTLY idx_detection_recent ON public.detection 
(startdate, enddate, site_id, probability)
WHERE probability IS NOT NULL 
  AND startdate >= '2023-08-01';

-- Site table optimization
CREATE INDEX IF NOT EXISTS idx_site_id ON public.site (id);

-- Add geometry column to site table
ALTER TABLE public.site ADD COLUMN geom geometry(Point, 4326);
UPDATE public.site SET geom = ST_Point(x, y);
CREATE INDEX idx_site_geom ON public.site USING GIST (geom);
