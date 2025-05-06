CREATE SEQUENCE IF NOT EXISTS public.detection_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS public.detection
(
    id integer NOT NULL DEFAULT nextval('detection_id_seq'::regclass),
    site_id text COLLATE pg_catalog."default" NOT NULL,
    model_id integer,
    label text COLLATE pg_catalog."default",
    eventtype text COLLATE pg_catalog."default",
    probability numeric,
    startdate timestamp with time zone NOT NULL,
    enddate timestamp with time zone NOT NULL,
    detection_id integer,
    CONSTRAINT detection_pkey PRIMARY KEY (id),
    CONSTRAINT detection_site_id_detection_id_model_id_key UNIQUE (site_id, detection_id, model_id),
    CONSTRAINT detection_model_fk FOREIGN KEY (model_id)
        REFERENCES public.model (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT detection_site_fk FOREIGN KEY (site_id)
        REFERENCES public.site (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.detection
    OWNER to mmgis;