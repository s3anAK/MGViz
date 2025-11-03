CREATE SEQUENCE IF NOT EXISTS public.weather_event_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

CREATE TABLE IF NOT EXISTS public.weather_event
(
    id integer NOT NULL DEFAULT nextval('weather_event_id_seq'::regclass),
    eventname text COLLATE pg_catalog."default" NOT NULL,
    startdate timestamp with time zone NOT NULL,
    enddate timestamp with time zone NOT NULL,
    CONSTRAINT weather_event_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.weather_event
    OWNER to mmgis;