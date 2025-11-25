CREATE TABLE IF NOT EXISTS public.site
(
    id text COLLATE pg_catalog."default" NOT NULL,
    x numeric,
    y numeric,
    geom geometry(Point,4326),
    startdate timestamp with time zone,
    enddate timestamp with time zone,
    CONSTRAINT site_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.site
    OWNER to mmgis;


CREATE INDEX IF NOT EXISTS idx_site_geom
    ON public.site USING gist
    (geom)
    TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_site_id
    ON public.site USING btree
    (id COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;