CREATE TABLE IF NOT EXISTS public.troposphere
(
    id integer NOT NULL DEFAULT nextval('troposphere_id_seq'::regclass),
    site text COLLATE pg_catalog."default" NOT NULL,
    time_utc timestamp with time zone,
    trotot numeric,
    trototstdev numeric,
    trodry numeric,
    trodrystdev numeric,
    trowet numeric,
    trowetstdev numeric,
    tgnwet numeric,
    tgnwetstdev numeric,
    tgewet numeric,
    tgewetstdev numeric,
    iwv numeric,
    press numeric,
    temdry numeric,
    CONSTRAINT troposphere_pkey PRIMARY KEY (id),
    CONSTRAINT site_time_utc_unique UNIQUE (site, time_utc),
    CONSTRAINT site_fk FOREIGN KEY (site)
        REFERENCES public.site (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.troposphere
    OWNER to mmgis;