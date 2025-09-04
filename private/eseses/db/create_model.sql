CREATE SEQUENCE IF NOT EXISTS public.model_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS public.model
(
    id integer NOT NULL DEFAULT nextval('model_id_seq'::regclass),
    name text COLLATE pg_catalog."default" NOT NULL,
    mode text COLLATE pg_catalog."default" NOT NULL,
    probability_threshold numeric,
    CONSTRAINT model_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.model
    OWNER to mmgis;