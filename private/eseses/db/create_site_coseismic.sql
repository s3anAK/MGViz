CREATE TABLE IF NOT EXISTS public.site_coseismic
(
    site_id text COLLATE pg_catalog."default" NOT NULL,
    coseismic_id integer NOT NULL,
    neu text COLLATE pg_catalog."default",
    CONSTRAINT site_coseismic_pkey PRIMARY KEY (site_id, coseismic_id),
    CONSTRAINT coseismic_site_fk FOREIGN KEY (coseismic_id)
        REFERENCES public.coseismic (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT site_coseismic_fk FOREIGN KEY (site_id)
        REFERENCES public.site (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.site_coseismic
    OWNER to mmgis;