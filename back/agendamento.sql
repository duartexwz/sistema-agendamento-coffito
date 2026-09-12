--
-- PostgreSQL database dump
--

\restrict NfvCgXrN8ataqlxQLOErHFBhQd0B7203leUpb5ZsfaZnfx2NsZqj8KJKlsriJtm

-- Dumped from database version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: acesso_enum; Type: TYPE; Schema: public; Owner: Coffito@admin
--

CREATE TYPE public.acesso_enum AS ENUM (
    'evento_admin',
    'master',
    'colaborador'
);


ALTER TYPE public.acesso_enum OWNER TO "Coffito@admin";

--
-- Name: status_enum; Type: TYPE; Schema: public; Owner: Coffito@admin
--

CREATE TYPE public.status_enum AS ENUM (
    'pendente',
    'tramite',
    'aprovado',
    'cancelado',
    'recusado'
);


ALTER TYPE public.status_enum OWNER TO "Coffito@admin";

--
-- Name: status_usuario_enum; Type: TYPE; Schema: public; Owner: Coffito@admin
--

CREATE TYPE public.status_usuario_enum AS ENUM (
    'ativo',
    'inativo'
);


ALTER TYPE public.status_usuario_enum OWNER TO "Coffito@admin";

--
-- Name: tipo_apoio_enum; Type: TYPE; Schema: public; Owner: Coffito@admin
--

CREATE TYPE public.tipo_apoio_enum AS ENUM (
    'profissional',
    'sala de cursos',
    'utilizacao_auditorio',
    'plenaria'
);


ALTER TYPE public.tipo_apoio_enum OWNER TO "Coffito@admin";

--
-- Name: tipo_usuario_enum; Type: TYPE; Schema: public; Owner: Coffito@admin
--

CREATE TYPE public.tipo_usuario_enum AS ENUM (
    'colaborador',
    'estagiario',
    'conselheiro',
    'menor_aprendiz'
);


ALTER TYPE public.tipo_usuario_enum OWNER TO "Coffito@admin";

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: cargos; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.cargos (
    id integer NOT NULL,
    nome character varying(70)
);


ALTER TABLE public.cargos OWNER TO "Coffito@admin";

--
-- Name: cargos_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.cargos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cargos_id_seq OWNER TO "Coffito@admin";

--
-- Name: cargos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.cargos_id_seq OWNED BY public.cargos.id;


--
-- Name: espacos; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.espacos (
    id integer NOT NULL,
    nome character varying(255) NOT NULL,
    descricao character varying(255),
    localizacao character varying(150),
    capacidade_minima integer,
    capacidade_maxima integer,
    ativo boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT date_trunc('second'::text, (now() AT TIME ZONE 'America/Sao_Paulo'::text)),
    updated_at timestamp without time zone DEFAULT date_trunc('second'::text, (now() AT TIME ZONE 'America/Sao_Paulo'::text))
);


ALTER TABLE public.espacos OWNER TO "Coffito@admin";

--
-- Name: espacos_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.espacos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.espacos_id_seq OWNER TO "Coffito@admin";

--
-- Name: espacos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.espacos_id_seq OWNED BY public.espacos.id;


--
-- Name: historico_reservas; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.historico_reservas (
    id integer NOT NULL,
    reserva_id integer,
    usuario_id integer,
    status_anterior_id integer,
    status_novo_id integer,
    acao character varying(100),
    observacao text,
    created_at timestamp without time zone DEFAULT date_trunc('second'::text, (now() AT TIME ZONE 'America/Sao_Paulo'::text))
);


ALTER TABLE public.historico_reservas OWNER TO "Coffito@admin";

--
-- Name: auditoria_logs; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.auditoria_logs (
    id SERIAL PRIMARY KEY,
    ator_usuario_id integer,
    ator_nome character varying(255),
    ator_email character varying(255),
    entidade_tipo character varying(50) NOT NULL,
    entidade_id integer,
    acao character varying(100) NOT NULL,
    descricao text NOT NULL,
    dados_antes jsonb,
    dados_depois jsonb,
    metadata jsonb,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp without time zone DEFAULT date_trunc('second'::text, (now() AT TIME ZONE 'America/Sao_Paulo'::text))
);


ALTER TABLE public.auditoria_logs OWNER TO "Coffito@admin";

--
-- Name: reservas_status_historico; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.reservas_status_historico (
    id integer NOT NULL,
    reserva_id integer NOT NULL,
    status_anterior character varying(50),
    status_novo character varying(50) NOT NULL,
    alterado_por integer,
    alterado_em timestamp without time zone DEFAULT date_trunc('second'::text, (now() AT TIME ZONE 'America/Sao_Paulo'::text))
);


ALTER TABLE public.reservas_status_historico OWNER TO "Coffito@admin";

--
-- Name: reservas_status_historico_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.reservas_status_historico_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reservas_status_historico_id_seq OWNER TO "Coffito@admin";

--
-- Name: reservas_status_historico_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.reservas_status_historico_id_seq OWNED BY public.reservas_status_historico.id;


--
-- Name: historico_reservas_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.historico_reservas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.historico_reservas_id_seq OWNER TO "Coffito@admin";

--
-- Name: historico_reservas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.historico_reservas_id_seq OWNED BY public.historico_reservas.id;


--
-- Name: niveis_acesso; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.niveis_acesso (
    id integer NOT NULL,
    nome character varying(50)
);


ALTER TABLE public.niveis_acesso OWNER TO "Coffito@admin";

--
-- Name: niveis_acesso_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.niveis_acesso_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.niveis_acesso_id_seq OWNER TO "Coffito@admin";

--
-- Name: niveis_acesso_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.niveis_acesso_id_seq OWNED BY public.niveis_acesso.id;


--
-- Name: recursos; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.recursos (
    id integer NOT NULL,
    nome character varying(150) NOT NULL,
    quantidade integer,
    disponivel boolean DEFAULT true
);


ALTER TABLE public.recursos OWNER TO "Coffito@admin";

--
-- Name: recursos_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.recursos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.recursos_id_seq OWNER TO "Coffito@admin";

--
-- Name: recursos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.recursos_id_seq OWNED BY public.recursos.id;


--
-- Name: reserva_recursos; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.reserva_recursos (
    id integer NOT NULL,
    reserva_id integer,
    recurso_id integer,
    quantidade integer
);


ALTER TABLE public.reserva_recursos OWNER TO "Coffito@admin";

--
-- Name: reserva_recursos_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.reserva_recursos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reserva_recursos_id_seq OWNER TO "Coffito@admin";

--
-- Name: reserva_recursos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.reserva_recursos_id_seq OWNED BY public.reserva_recursos.id;


--
-- Name: reservas; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.reservas (
    id integer NOT NULL,
    protocolo character varying(255),
    solicitante_id integer,
    espaco_solicitado_id integer,
    espaco_aprovado_id integer,
    status_id integer,
    nome_evento character varying(255) NOT NULL,
    objetivo text,
    data_inicio date NOT NULL,
    data_fim date NOT NULL,
    horario_inicio time without time zone NOT NULL,
    horario_fim time without time zone NOT NULL,
    quantidade_participantes integer NOT NULL,
    observacoes text,
    analisado_por integer,
    criado_por integer,
    created_at timestamp without time zone DEFAULT date_trunc('second'::text, (now() AT TIME ZONE 'America/Sao_Paulo'::text)),
    updated_at timestamp without time zone DEFAULT date_trunc('second'::text, (now() AT TIME ZONE 'America/Sao_Paulo'::text)),
    solicitante_nome character varying(2550),
    solicitante_cpf character varying(11),
    solicitante_email character varying(255),
    solicitante_telefone character varying(14),
    solicitante_profissao character varying(150)
);


ALTER TABLE public.reservas OWNER TO "Coffito@admin";

--
-- Name: reservas_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.reservas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reservas_id_seq OWNER TO "Coffito@admin";

--
-- Name: reservas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.reservas_id_seq OWNED BY public.reservas.id;


--
-- Name: setor_solicitante; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.setor_solicitante (
    id integer NOT NULL,
    nome character varying(70)
);


ALTER TABLE public.setor_solicitante OWNER TO "Coffito@admin";

--
-- Name: setor_solicitante_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.setor_solicitante_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.setor_solicitante_id_seq OWNER TO "Coffito@admin";

--
-- Name: setor_solicitante_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.setor_solicitante_id_seq OWNED BY public.setor_solicitante.id;


--
-- Name: status_reservas; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.status_reservas (
    id integer NOT NULL,
    nome character varying(50)
);


ALTER TABLE public.status_reservas OWNER TO "Coffito@admin";

--
-- Name: status_reservas_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.status_reservas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.status_reservas_id_seq OWNER TO "Coffito@admin";

--
-- Name: status_reservas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.status_reservas_id_seq OWNED BY public.status_reservas.id;


--
-- Name: suporte; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.suporte (
    id integer NOT NULL,
    reserva_id integer,
    outros text,
    coffe_break boolean DEFAULT false,
    backdrop boolean DEFAULT false,
    evento_ornamentado boolean DEFAULT false
);


ALTER TABLE public.suporte OWNER TO "Coffito@admin";

--
-- Name: suporte_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.suporte_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.suporte_id_seq OWNER TO "Coffito@admin";

--
-- Name: suporte_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.suporte_id_seq OWNED BY public.suporte.id;


--
-- Name: tipos_usuarios; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.tipos_usuarios (
    id integer NOT NULL,
    nome character varying(50)
);


ALTER TABLE public.tipos_usuarios OWNER TO "Coffito@admin";

--
-- Name: tipos_usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.tipos_usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipos_usuarios_id_seq OWNER TO "Coffito@admin";

--
-- Name: tipos_usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.tipos_usuarios_id_seq OWNED BY public.tipos_usuarios.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: Coffito@admin
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nome character varying(255) NOT NULL,
    tipo_usuario_id integer,
    niveis_acesso_id integer,
    matricula character varying(50),
    setor_solicitante_id integer,
    cargo_id integer,
    cpf character varying(11) NOT NULL,
    email character varying(255) NOT NULL,
    telefone character varying(11) NOT NULL,
    password character varying(255) NOT NULL,
    ativo boolean DEFAULT true,
    updated_by integer NOT NULL,
    created_at timestamp without time zone DEFAULT date_trunc('second'::text, (now() AT TIME ZONE 'America/Sao_Paulo'::text)),
    updated_at timestamp without time zone DEFAULT date_trunc('second'::text, (now() AT TIME ZONE 'America/Sao_Paulo'::text))
);


ALTER TABLE public.usuarios OWNER TO "Coffito@admin";

--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: Coffito@admin
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO "Coffito@admin";

--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: Coffito@admin
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: cargos id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.cargos ALTER COLUMN id SET DEFAULT nextval('public.cargos_id_seq'::regclass);


--
-- Name: espacos id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.espacos ALTER COLUMN id SET DEFAULT nextval('public.espacos_id_seq'::regclass);


--
-- Name: historico_reservas id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.historico_reservas ALTER COLUMN id SET DEFAULT nextval('public.historico_reservas_id_seq'::regclass);


--
-- Name: reservas_status_historico id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas_status_historico ALTER COLUMN id SET DEFAULT nextval('public.reservas_status_historico_id_seq'::regclass);


--
-- Name: niveis_acesso id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.niveis_acesso ALTER COLUMN id SET DEFAULT nextval('public.niveis_acesso_id_seq'::regclass);


--
-- Name: recursos id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.recursos ALTER COLUMN id SET DEFAULT nextval('public.recursos_id_seq'::regclass);


--
-- Name: reserva_recursos id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reserva_recursos ALTER COLUMN id SET DEFAULT nextval('public.reserva_recursos_id_seq'::regclass);


--
-- Name: reservas id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas ALTER COLUMN id SET DEFAULT nextval('public.reservas_id_seq'::regclass);


--
-- Name: setor_solicitante id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.setor_solicitante ALTER COLUMN id SET DEFAULT nextval('public.setor_solicitante_id_seq'::regclass);


--
-- Name: status_reservas id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.status_reservas ALTER COLUMN id SET DEFAULT nextval('public.status_reservas_id_seq'::regclass);


--
-- Name: suporte id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.suporte ALTER COLUMN id SET DEFAULT nextval('public.suporte_id_seq'::regclass);


--
-- Name: tipos_usuarios id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.tipos_usuarios ALTER COLUMN id SET DEFAULT nextval('public.tipos_usuarios_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Data for Name: cargos; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.cargos (id, nome) FROM stdin;
1	Estagiário
2	MENOR APRENDIZ
3	Chefe de Setor
7	Teste LOGGING 2
8	Teste LOGGING 3
9	Teste 4
\.


--
-- Data for Name: espacos; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.espacos (id, nome, descricao, localizacao, capacidade_minima, capacidade_maxima, ativo, created_at, updated_at) FROM stdin;
1	Sala de Cursos	Sala de cursos para eventos médios e pequenos	3º andar	1	100	t	2026-08-21 21:59:06	2026-08-21 21:59:06
\.


--
-- Data for Name: historico_reservas; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.historico_reservas (id, reserva_id, usuario_id, status_anterior_id, status_novo_id, acao, observacao, created_at) FROM stdin;
\.


--
-- Data for Name: reservas_status_historico; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.reservas_status_historico (id, reserva_id, status_anterior, status_novo, alterado_por, alterado_em) FROM stdin;
\.


--
-- Data for Name: niveis_acesso; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.niveis_acesso (id, nome) FROM stdin;
1	ADMINISTRADOR
2	COLABORADOR
3	MASTER
4	OPERADOR
\.


--
-- Data for Name: recursos; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.recursos (id, nome, quantidade, disponivel) FROM stdin;
\.


--
-- Data for Name: reserva_recursos; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.reserva_recursos (id, reserva_id, recurso_id, quantidade) FROM stdin;
\.


--
-- Data for Name: reservas; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.reservas (id, protocolo, solicitante_id, espaco_solicitado_id, espaco_aprovado_id, status_id, nome_evento, objetivo, data_inicio, data_fim, horario_inicio, horario_fim, quantidade_participantes, observacoes, analisado_por, criado_por, created_at, updated_at, solicitante_nome, solicitante_cpf, solicitante_email, solicitante_telefone, solicitante_profissao) FROM stdin;
29	22 2026 29	\N	1	1	3	string	\N	2026-08-22	2026-08-22	14:54:46.664	14:54:46.664	0	\N	\N	\N	2026-08-22 12:19:21	2026-08-22 12:19:21	\N	\N	\N	\N	\N
30	22 2026 30	\N	1	1	3	string	\N	2026-08-22	2026-08-22	14:54:46.664	14:54:46.664	0	\N	\N	\N	2026-08-22 12:19:35	2026-08-22 12:19:35	\N	\N	\N	\N	\N
31	23 2026 31	\N	1	1	3	string	\N	2026-08-23	2026-08-23	18:59:36.459	18:59:36.459	0	\N	\N	\N	2026-08-23 15:59:54	2026-08-23 15:59:54	\N	\N	\N	\N	\N
32	23 2026 32	\N	1	1	3	string	\N	2026-08-23	2026-08-23	19:10:05.693	19:10:05.693	0	\N	\N	\N	2026-08-23 16:10:13	2026-08-23 16:10:13	\N	\N	\N	\N	\N
33	23 2026 33	\N	1	1	3	Evento Teste Externo	Teste	2026-08-23	2026-08-23	08:47:11.485	09:47:11.485	100	Teste	\N	\N	2026-08-23 17:48:15	2026-08-23 17:48:15	\N	\N	\N	\N	\N
\.


--
-- Data for Name: setor_solicitante; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.setor_solicitante (id, nome) FROM stdin;
1	SETIN
2	DAGEP
\.


--
-- Data for Name: status_reservas; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.status_reservas (id, nome) FROM stdin;
1	Aprovado
2	Negado
3	Pendente
4	Cancelado
\.


--
-- Data for Name: suporte; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.suporte (id, reserva_id, outros, coffe_break, backdrop, evento_ornamentado) FROM stdin;
\.


--
-- Data for Name: tipos_usuarios; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.tipos_usuarios (id, nome) FROM stdin;
5	Externo
6	Interno
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: Coffito@admin
--

COPY public.usuarios (id, nome, tipo_usuario_id, niveis_acesso_id, matricula, setor_solicitante_id, cargo_id, cpf, email, telefone, password, ativo, updated_by, created_at, updated_at) FROM stdin;
22	Usuário Teste Update	6	\N	\N	\N	\N	00000000000	usuarioteste@gmail.com	61984092729	$argon2id$v=19$m=65536,t=3,p=4$QfuKuL/2Ofzr45uUIwayIQ$ZvNDOvt4wgMLYkAm1ex1pr/3KU0uBUDR76ai0S7lvCs	t	0	2026-08-23 16:16:05	2026-08-23 16:16:05
18	Mayckon Kennedy Santos Carvalho Duarte	6	3	000146	1	1	71207195138	mayckon.duarte@coffito.gov.br	61984092729	$argon2id$v=19$m=65536,t=3,p=4$YfnngbsVjQ7Upsc0HTnS5A$ELeQy5nQwKGPZX28lowxUmYCLi/wxVw5yMm8jCgQJwI	t	0	2026-08-20 14:23:18	2026-08-20 14:23:18
\.


--
-- Name: cargos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.cargos_id_seq', 9, true);


--
-- Name: espacos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.espacos_id_seq', 2, true);


--
-- Name: historico_reservas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.historico_reservas_id_seq', 1, false);


--
-- Name: reservas_status_historico_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.reservas_status_historico_id_seq', 1, false);


--
-- Name: niveis_acesso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.niveis_acesso_id_seq', 7, true);


--
-- Name: recursos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.recursos_id_seq', 1, false);


--
-- Name: reserva_recursos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.reserva_recursos_id_seq', 1, false);


--
-- Name: reservas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.reservas_id_seq', 34, true);


--
-- Name: setor_solicitante_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.setor_solicitante_id_seq', 5, true);


--
-- Name: status_reservas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.status_reservas_id_seq', 5, true);


--
-- Name: suporte_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.suporte_id_seq', 1, false);


--
-- Name: tipos_usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.tipos_usuarios_id_seq', 7, true);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: Coffito@admin
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 22, true);


--
-- Name: cargos cargos_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.cargos
    ADD CONSTRAINT cargos_pkey PRIMARY KEY (id);


--
-- Name: espacos espacos_nome_key; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.espacos
    ADD CONSTRAINT espacos_nome_key UNIQUE (nome);


--
-- Name: espacos espacos_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.espacos
    ADD CONSTRAINT espacos_pkey PRIMARY KEY (id);


--
-- Name: historico_reservas historico_reservas_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.historico_reservas
    ADD CONSTRAINT historico_reservas_pkey PRIMARY KEY (id);


--
-- Name: reservas_status_historico reservas_status_historico_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas_status_historico
    ADD CONSTRAINT reservas_status_historico_pkey PRIMARY KEY (id);


--
-- Name: auditoria_logs idx_auditoria_logs_created_at; Type: INDEX; Schema: public; Owner: Coffito@admin
--

CREATE INDEX idx_auditoria_logs_created_at ON public.auditoria_logs USING btree (created_at DESC);


--
-- Name: auditoria_logs idx_auditoria_logs_ator_usuario_id; Type: INDEX; Schema: public; Owner: Coffito@admin
--

CREATE INDEX idx_auditoria_logs_ator_usuario_id ON public.auditoria_logs USING btree (ator_usuario_id);


--
-- Name: auditoria_logs idx_auditoria_logs_entidade; Type: INDEX; Schema: public; Owner: Coffito@admin
--

CREATE INDEX idx_auditoria_logs_entidade ON public.auditoria_logs USING btree (entidade_tipo, entidade_id);


--
-- Name: auditoria_logs idx_auditoria_logs_acao; Type: INDEX; Schema: public; Owner: Coffito@admin
--

CREATE INDEX idx_auditoria_logs_acao ON public.auditoria_logs USING btree (acao);


--
-- Name: reservas_status_historico idx_reservas_status_historico_reserva_id; Type: INDEX; Schema: public; Owner: Coffito@admin
--

CREATE INDEX idx_reservas_status_historico_reserva_id ON public.reservas_status_historico USING btree (reserva_id);


--
-- Name: reservas_status_historico idx_reservas_status_historico_alterado_por; Type: INDEX; Schema: public; Owner: Coffito@admin
--

CREATE INDEX idx_reservas_status_historico_alterado_por ON public.reservas_status_historico USING btree (alterado_por);


--
-- Name: niveis_acesso niveis_acesso_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.niveis_acesso
    ADD CONSTRAINT niveis_acesso_pkey PRIMARY KEY (id);


--
-- Name: recursos recursos_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.recursos
    ADD CONSTRAINT recursos_pkey PRIMARY KEY (id);


--
-- Name: reserva_recursos reserva_recursos_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reserva_recursos
    ADD CONSTRAINT reserva_recursos_pkey PRIMARY KEY (id);


--
-- Name: reservas reservas_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT reservas_pkey PRIMARY KEY (id);


--
-- Name: setor_solicitante setor_solicitante_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.setor_solicitante
    ADD CONSTRAINT setor_solicitante_pkey PRIMARY KEY (id);


--
-- Name: status_reservas status_reservas_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.status_reservas
    ADD CONSTRAINT status_reservas_pkey PRIMARY KEY (id);


--
-- Name: suporte suporte_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.suporte
    ADD CONSTRAINT suporte_pkey PRIMARY KEY (id);


--
-- Name: tipos_usuarios tipos_usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.tipos_usuarios
    ADD CONSTRAINT tipos_usuarios_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_cpf_key; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_cpf_key UNIQUE (cpf);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_matricula_key; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_matricula_key UNIQUE (matricula);


--
-- Name: usuarios usuarios_nome_key; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_nome_key UNIQUE (nome);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: usuarios fk_cargo_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_cargo_id FOREIGN KEY (cargo_id) REFERENCES public.cargos(id) ON DELETE SET NULL;


--
-- Name: usuarios fk_cargos_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_cargos_id FOREIGN KEY (cargo_id) REFERENCES public.cargos(id);


--
-- Name: reservas fk_espaco_aprovado_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT fk_espaco_aprovado_id FOREIGN KEY (espaco_aprovado_id) REFERENCES public.espacos(id);


--
-- Name: reservas fk_espaco_solicitado_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT fk_espaco_solicitado_id FOREIGN KEY (espaco_solicitado_id) REFERENCES public.espacos(id);


--
-- Name: usuarios fk_niveis_acesso; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_niveis_acesso FOREIGN KEY (niveis_acesso_id) REFERENCES public.niveis_acesso(id) ON DELETE SET NULL;


--
-- Name: usuarios fk_niveis_acesso_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_niveis_acesso_id FOREIGN KEY (niveis_acesso_id) REFERENCES public.niveis_acesso(id) ON DELETE SET NULL;


--
-- Name: reserva_recursos fk_recurso_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reserva_recursos
    ADD CONSTRAINT fk_recurso_id FOREIGN KEY (recurso_id) REFERENCES public.recursos(id);


--
-- Name: historico_reservas fk_reserva_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.historico_reservas
    ADD CONSTRAINT fk_reserva_id FOREIGN KEY (reserva_id) REFERENCES public.reservas(id);


--
-- Name: reservas_status_historico fk_reservas_status_historico_reserva_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas_status_historico
    ADD CONSTRAINT fk_reservas_status_historico_reserva_id FOREIGN KEY (reserva_id) REFERENCES public.reservas(id);


--
-- Name: reserva_recursos fk_reserva_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reserva_recursos
    ADD CONSTRAINT fk_reserva_id FOREIGN KEY (reserva_id) REFERENCES public.reservas(id);


--
-- Name: suporte fk_reserva_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.suporte
    ADD CONSTRAINT fk_reserva_id FOREIGN KEY (reserva_id) REFERENCES public.reservas(id);


--
-- Name: usuarios fk_setor_solicitante_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_setor_solicitante_id FOREIGN KEY (setor_solicitante_id) REFERENCES public.setor_solicitante(id) ON DELETE SET NULL;


--
-- Name: reservas fk_solicitante_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT fk_solicitante_id FOREIGN KEY (solicitante_id) REFERENCES public.usuarios(id);


--
-- Name: reservas fk_criado_por; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT fk_criado_por FOREIGN KEY (criado_por) REFERENCES public.usuarios(id);


--
-- Name: historico_reservas fk_status_anterior_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.historico_reservas
    ADD CONSTRAINT fk_status_anterior_id FOREIGN KEY (status_anterior_id) REFERENCES public.status_reservas(id);


--
-- Name: reservas fk_status_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas
    ADD CONSTRAINT fk_status_id FOREIGN KEY (status_id) REFERENCES public.status_reservas(id);


--
-- Name: historico_reservas fk_status_novo_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.historico_reservas
    ADD CONSTRAINT fk_status_novo_id FOREIGN KEY (status_novo_id) REFERENCES public.status_reservas(id);


--
-- Name: usuarios fk_tipo_usuario_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_tipo_usuario_id FOREIGN KEY (tipo_usuario_id) REFERENCES public.tipos_usuarios(id) ON DELETE SET NULL;


--
-- Name: historico_reservas fk_usuario_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.historico_reservas
    ADD CONSTRAINT fk_usuario_id FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: reservas_status_historico fk_reservas_status_historico_alterado_por; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.reservas_status_historico
    ADD CONSTRAINT fk_reservas_status_historico_alterado_por FOREIGN KEY (alterado_por) REFERENCES public.usuarios(id);


--
-- Name: auditoria_logs fk_auditoria_ator_usuario_id; Type: FK CONSTRAINT; Schema: public; Owner: Coffito@admin
--

ALTER TABLE ONLY public.auditoria_logs
    ADD CONSTRAINT fk_auditoria_ator_usuario_id FOREIGN KEY (ator_usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict NfvCgXrN8ataqlxQLOErHFBhQd0B7203leUpb5ZsfaZnfx2NsZqj8KJKlsriJtm

