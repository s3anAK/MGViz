-- Increase work memory for complex queries
SET work_mem = '256MB'; -- 4MB default

-- Main performance index
CREATE INDEX idx_detection_performance ON public.detection 
(model_id, site_id, startdate, enddate) 
WHERE probability IS NOT NULL;

-- Model filtering
CREATE INDEX idx_model_mode_name ON public.model (mode, name);

-- Date range queries  
CREATE INDEX idx_detection_dates ON public.detection (startdate, enddate);

-- Window function optimization
CREATE INDEX idx_detection_site_enddate ON public.detection (site_id, enddate DESC);

-- Satisfy DISTINCT ON ordering without a sort
CREATE INDEX CONCURRENTLY ix_detection_site_enddate_desc
    ON public.detection (site_id, enddate DESC)
    INCLUDE (model_id, probability, startdate, enddate);

-- Add geometry column to site table
ALTER TABLE public.site ADD COLUMN geom geometry(Point, 4326);
UPDATE public.site SET geom = ST_Point(x, y);
CREATE INDEX idx_site_geom ON public.site USING GIST (geom);
