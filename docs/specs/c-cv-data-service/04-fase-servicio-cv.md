# 04 — Fase C: Lambda `cv` (lectura del CV)

[<- 03 Fase B](03-fase-migracion-handlers.md) | [Siguiente: Fase D ->](05-fase-consumo-apps.md)

## Objetivo

Crear `serverless/lambda/services/cv/` siguiendo el estandar
`lambda-controller`: un Lambda HTTP read-only que sirve el CV desde Neon via
`GET /cv`.

Depende de la Fase A. Requiere la precondicion del seed para la verificacion
E2E (la suite unit usa fixtures, no necesita el seed).

## Contrato del API

Un solo path `GET /cv`. `operation` es siempre `cv`; `action` selecciona que
devolver:

| Request | Devuelve |
|---------|----------|
| `GET /cv?operation=cv&action=get&niche=<n>&locale=<l>` | CV completo |
| `GET /cv?operation=cv&action=profile&locale=<l>` | Profile + stats |
| `GET /cv?operation=cv&action=experiences&niche=<n>&locale=<l>` | Experiencias |
| `GET /cv?operation=cv&action=projects&niche=<n>&locale=<l>` | Proyectos |
| `GET /cv?operation=cv&action=certificates&niche=<n>` | Certificados |
| `GET /cv?operation=cv&action=awards&niche=<n>&locale=<l>` | Premios |
| `GET /cv?operation=cv&action=education&niche=<n>&locale=<l>` | Educacion |
| `GET /cv?operation=cv&action=languages&niche=<n>&locale=<l>` | Idiomas |
| `GET /cv?operation=cv&action=references&niche=<n>&locale=<l>` | Referencias |
| `GET /cv?operation=cv&action=skills&niche=<n>&locale=<l>` | Skill categories |

Parametros:
- `niche` — opcional. Uno de `fintech|architect|leader|vibe|generic`. Sin
  niche -> sin filtro (todo). Filtra via las uniones `<entidad>_niches`.
- `locale` — opcional, default `es`. `es|en`. Selecciona la fila de
  `translations` por `locale`.

## Estructura del Lambda

```text
serverless/lambda/services/cv/
├── manifest.yaml          # ver abajo
├── .gitignore             # build/ + build.zip
├── pyproject.toml         # deps runtime + grupo dev
├── core/
│   ├── handler.py         # delega en http_handler (cors_origin='public')
│   ├── controllers/cv/
│   │   ├── get.py          # action 'get'  -> Get(BaseController)
│   │   ├── profile.py      # action 'profile'
│   │   ├── experiences.py  # action 'experiences'
│   │   ├── projects.py     # action 'projects'
│   │   ├── certificates.py
│   │   ├── awards.py
│   │   ├── education.py
│   │   ├── languages.py
│   │   ├── references.py
│   │   └── skills.py
│   ├── services/
│   │   └── cv_service.py   # orquesta: delega en shared.db.cv_repository
│   ├── models/
│   │   └── cv.py           # modelos Pydantic: CvQueryModel (niche, locale)
│   └── settings/
│       ├── config.py       # AppConfig
│       └── operations.py   # OPERATIONS = {'cv': {...}}
├── events/                 # un JSON por action para `serverless run`
│   ├── get.json
│   ├── experiences.json
│   └── ...
└── tests/
    ├── conftest.py
    ├── unit/
    └── integration/
```

> El Lambda comparte el "kit" via `shared.lambda_kit` — no duplica
> `base_controller` etc. (variante del backend del portfolio, ver
> `.claude/rules/lambda-controller.md`).

### `manifest.yaml`

```yaml
name: cv
description: Sirve el CV (lectura) desde Neon PostgreSQL via GET /cv.
runtime: python3.13
handler: core.handler.lambda_handler
memory: 512
timeout: 30
trigger:
  type: http
  method: GET
  path: /cv
uses:
  tables:
    cache: read-write          # @cached de las respuestas del CV
  secrets:
    - neon-url                 # connection string PostgreSQL (SecureString)
  sends-email: false
env:
  default:
    LOG_LEVEL: INFO
  dev:
    CORS_ALLOWED_ORIGINS: '<6 subdominios dev>'
  stage:
    CORS_ALLOWED_ORIGINS: '<6 subdominios stage>'
  prod:
    LOG_LEVEL: WARNING
    CORS_ALLOWED_ORIGINS: '<6 subdominios prod>'
```

> `neon-url` es el secreto que ya usa `stream_processor`. `cv` lo necesita
> para `shared.db.session`. Verificar que `provisioner.py` mapee el secreto
> `neon-url` a la env var que `shared.db.url` espera (`SSM_NEON_URL_PATH` /
> `DATABASE_URL`). Si el manifiesto de `cv` declara `neon-url`, el provisioner
> ya inyecta el path SSM — mismo patron que `db` y `stream_processor`.

## `shared/db/cv_repository.py` (NUEVO)

Las queries de lectura del CV. El `core/` del Lambda `cv` NO importa
`sqlalchemy` — consume estas funciones. Hermano de `repository.py`.

Funciones (todas reciben `*, niche: str | None, locale: str = 'es'`):

- `get_profile(*, locale)` — `Profile` + `ProfileStats` + textos de
  `translations` (`entity_type='profile'`).
- `list_experiences(*, niche, locale)` — `Experience` + bullets + skills +
  textos, ordenadas por `niche_priorities.priority` desc.
- `list_projects(*, niche, locale)` — `Project` + case study + metrics +
  tech tags + textos.
- `list_certificates(*, niche)`, `list_awards(*, niche, locale)`,
  `list_education(*, niche, locale)`, `list_languages(*, niche, locale)`,
  `list_references(*, niche, locale)`, `list_skill_categories(*, niche,
  locale)`.
- `get_full_cv(*, niche, locale)` — orquesta todas las anteriores en un solo
  dict (action `get`).

Patron de resolucion de textos bilingues: cada query hace JOIN/subquery a
`translations` filtrando por `entity_type`, `entity_id`, `locale`. El
resultado se aplana al shape que esperan los Zod schemas de
`@portfolio/content` (ver fase D). El filtro por niche es un JOIN a la union
`<entidad>_niches`.

Errores: levantan `RepositoryError` (ya existe en `repository.py`); el
`cv_service` los traduce a `ServiceError`.

## `core/services/cv_service.py`

Delega en `shared.db.cv_repository`, normaliza errores a `ServiceError`,
envuelve cada funcion con `@cached` (cache DynamoDB, TTL ~1h — el CV cambia
raramente). El service NO importa `sqlalchemy`.

## `core/controllers/cv/<action>.py`

Un controller por action. Cada uno:
1. Toma el `CvQueryModel` validado (`niche`, `locale`).
2. Llama a la funcion correspondiente del `cv_service`.
3. Normaliza la salida a `{is_valid, data, code}`.

`action='get'` -> `Get` controller -> `cv_service.get_full_cv`.
`action='experiences'` -> `Experiences` controller -> `cv_service.list_experiences`.
(El nombre de la clase es `action.capitalize()`.)

## `core/models/cv.py`

`CvQueryModel` Pydantic: `niche: str | None`, `locale: Literal['es','en'] =
'es'`. Valida que `niche` sea uno de los 5 validos o `None`. Los query params
llegan como strings; Pydantic castea.

## `core/handler.py`

Delega en `http_handler` con `cors_origin='public'` (el API lo consume el
prebuild de las apps; no hay credenciales), `success_status=200`,
`metric_names` de `cv`.

## Tests

Estandar lambda-controller — un archivo por escenario:

- `tests/unit/` — por cada action: test del modelo + service + controller +
  handler. Mockear `cv_repository` (E/S externa); NUNCA mockear el service o
  controller propios. `_helpers.py` con builders.
- `tests/integration/test_*_e2e.py` — `serverless tests --type=integration
  --lambda=cv` contra un branch Neon de prueba poblado con el seed. Cubre
  AC-4, AC-5, AC-6, AC-9.
- `shared`: `tests/unit/db/test_cv_repository_*.py` — las queries contra una
  DB de prueba.

## Verificacion de la fase

```bash
python -m compileall -q serverless/lambda/services/cv/core
python devtools/run.py serverless tests --type=unit --lambda=cv
python devtools/run.py serverless tests --type=coverage --lambda=cv
python devtools/run.py serverless lint-deps --lambda=cv
# ejecucion local (RIE) — requiere DATABASE_URL a un branch Neon poblado
python devtools/run.py serverless run --stage=local --lambda=cv \
  --event=events/get.json
```

Criterio: suite unit verde, coverage >= 80% per-file, `serverless run`
devuelve el CV (o colecciones vacias si la DB no esta poblada — ver AC-10).

## Done

- [ ] estructura del Lambda `cv` completa (estandar lambda-controller)
- [ ] `manifest.yaml` declara `trigger http GET /cv`, `cache`, secreto `neon-url`
- [ ] `shared/db/cv_repository.py` con las 10 funciones de lectura
- [ ] 10 controllers (un action cada uno) + `cv_service` + `CvQueryModel`
- [ ] `handler.py` delega en `http_handler`
- [ ] tests unit verdes, coverage >= 80%
- [ ] tests integration E2E verdes contra branch Neon poblado
- [ ] `events/*.json` por action

Continua en [05-fase-consumo-apps.md](05-fase-consumo-apps.md).
