CREATE SEQUENCE IF NOT EXISTS public.coseismic_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS public.coseismic
(
    id integer NOT NULL DEFAULT nextval('coseismic_id_seq'::regclass),
    time_utc timestamp with time zone,
    location text COLLATE pg_catalog."default",
    magnitude numeric,
    geom geometry(Point,4326),
    CONSTRAINT coseismic_pkey PRIMARY KEY (id),
    CONSTRAINT unique_coseismic UNIQUE (time_utc)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.coseismic
    OWNER to mmgis;