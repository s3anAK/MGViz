CREATE TABLE IF NOT EXISTS public.site
(
    id text COLLATE pg_catalog."default" NOT NULL,
    x numeric,
    y numeric,
    CONSTRAINT site_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.site
    OWNER to mmgis;