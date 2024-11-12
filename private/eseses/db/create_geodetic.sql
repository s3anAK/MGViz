CREATE TABLE IF NOT EXISTS public.geodetic
(
    id integer NOT NULL DEFAULT nextval('geodetic_id_seq'::regclass),
    site text COLLATE pg_catalog."default" NOT NULL,
    time_utc timestamp with time zone,
    source text COLLATE pg_catalog."default",
    type text COLLATE pg_catalog."default",
    filter text COLLATE pg_catalog."default",
    n numeric,
    e numeric,
    u numeric,
    CONSTRAINT geodetic_pkey PRIMARY KEY (id),
    CONSTRAINT geodetic_site_time_utc_unique UNIQUE (site, time_utc),
    CONSTRAINT site_fk FOREIGN KEY (site)
        REFERENCES public.site (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.geodetic
    OWNER to mmgis;