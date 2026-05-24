# 02. Diagramas: flujo y ER

> Secciones 4-5 del [plan-format](../../../.claude/rules/plan-format.md).

[← 01](01-contexto-y-decision.md) · [README](README.md) · [03 →](03-tests-requeridos.md)

## 4. Diagrama de flujo (antes y despues)

### Antes — pageview actual

```text
Browser (Astro)                 API Gateway (REGIONAL)              Lambda tracking_pixel              Neon
─────────────────────────────────────────────────────────────────────────────────────────────────────────
DOMContentLoaded                                                                                       
    │                                                                                                  
    ├─ buildTrackPayload                                                                              
    │   {operation, action, session_id, event_id,                                                     
    │    event_type_id, page_url, niche, event_props}                                                 
    │   ← 7 campos. NO captura: page_title, page_path,                                                
    │     referrer, utm_*, viewport_*, devicePixelRatio                                               
    │                                                                                                  
    ▼                                                                                                  
sendBeacon POST /track ────────► event['headers']                                                     
                                  cf-ipcountry: <NONE>                                                
                                  user-agent: <UA>                                                    
                                  x-forwarded-for: <IP>                                               
                                 (Regional GW NO inyecta                                              
                                  cloudfront-viewer-country)                                          
                                                            ────► extract_meta                        
                                                                   ip = X-Forwarded-For first         
                                                                   country = cf-ipcountry → None      
                                                                   user_agent = headers['user-agent'] 
                                                                                                       
                                                                  parse_user_agent (regex custom)     
                                                                   → browser, browser_version,        
                                                                     os, device_type                  
                                                                     (fails en WebView iOS, bots)     
                                                                                                       
                                                                  validate TrackEventModel            
                                                                   ← Optional fields todos None       
                                                                                                       
                                                                  save_tracking_event                 
                                                                   neon_payload[                      
                                                                     page_title=None,                 
                                                                     page_path=None,                  
                                                                     referrer=None,                   
                                                                     utm_*=None,                      
                                                                     viewport_*=None,                 
                                                                     country=None,                    
                                                                     browser_version=None,            
                                                                     stream_event_id=None  ← legacy   
                                                                   ]                                  
                                                                                                       
                                                                  insert_tracking ──────► INSERT INTO 
                                                                                          tracking_   
                                                                                          events     
                                                                                          (11 cols    
                                                                                           NULL)      
```

### Despues — pageview completo

```text
Browser (Astro 6 + ClientRouter)      API Gateway (EDGE-OPTIMIZED)        Lambda tracking_pixel        Neon
──────────────────────────────────────────────────────────────────────────────────────────────────────────
astro:page-load                                                                                       
    │                                                                                                  
    ├─ guard firstLoad (anti doble-disparo)                                                          
    │                                                                                                  
    ├─ buildTrackPayload                                                                              
    │   {operation, action, session_id, event_id, event_type_id,                                      
    │    page_url, page_title, page_path, referrer,                                                   
    │    utm_source, utm_medium, utm_campaign, utm_content,                                           
    │    viewport_width, viewport_height, devicePixelRatio,                                           
    │    niche, event_props}                                                                          
    │   ← 16 campos. utm_* parseados de URLSearchParams.                                              
    │     viewport leido de window.innerWidth/Height.                                                 
    │     Strings vacios cuando no aplica (nunca null).                                               
    │                                                                                                  
    ▼                                                                                                  
sendBeacon POST /track ────► CloudFront edge ───► API Gateway                                         
                              añade headers:        ──► event['headers']                              
                              cloudfront-viewer-country = US                                          
                              cloudfront-forwarded-proto = https                                      
                              user-agent = <UA real>                                                  
                                                                       extract_meta                   
                                                                        country = cloudfront-viewer-  
                                                                                  country → 'US'      
                                                                        user_agent = headers[...]     
                                                                                                       
                                                                       parse_user_agent (ua-parser)   
                                                                        → browser, browser_version,   
                                                                          os, device_type             
                                                                          (cubre WebView, bots OK)    
                                                                                                       
                                                                       validate TrackEventModel       
                                                                        ← 9 campos required           
                                                                          (HTTP 400 si falta alguno)  
                                                                                                       
                                                                       save_tracking_event            
                                                                        neon_payload sin              
                                                                        stream_event_id (columna      
                                                                        drop). Todos los campos       
                                                                        no-null.                      
                                                                                                       
                                                                       insert_tracking ──────► INSERT 
                                                                                                row    
                                                                                                con 28 
                                                                                                cols   
                                                                                                full   
```

### Diferencias clave

| Etapa | Antes | Despues |
|-------|-------|---------|
| Trigger frontend | `DOMContentLoaded` | `astro:page-load` (cubre SPA nav) |
| Campos del payload | 7 | 16 |
| Custom domain | Regional | Edge-Optimized |
| Country source | `cf-ipcountry` (siempre null) | `cloudfront-viewer-country` |
| UA parser | regex custom (~80 lineas) | `ua-parser` (uap-python) |
| Pydantic | 9 fields Optional | 9 fields Required (`''` ok) |
| Columna `stream_event_id` | Presente, siempre None | DROP |
| View transitions | OFF | ClientRouter activo |

## 5. Diagrama ER — `tracking_events`

Solo cambia esta tabla. El resto del schema queda intacto.

### Antes (28 columnas)

```text
tracking_events (RANGE PARTITION BY created_at)
─────────────────────────────────────────────────
PK logico: (session_id, page_id, created_at)
─────────────────────────────────────────────────
session_id          text       NOT NULL
page_id             uuid       NOT NULL
created_at          timestamptz NOT NULL  ← partition key
received_at         timestamptz NOT NULL
expires_at          timestamptz NULL
stream_event_id     text       NULL       ← legacy, drop
page_url            text       NULL
page_title          text       NULL       ← 11 columnas
page_path           text       NULL       ←  que vuelven
referrer            text       NULL       ←  no-null tras
utm_source          text       NULL       ←  el plan
utm_medium          text       NULL       ←
utm_campaign        text       NULL       ←
utm_content         text       NULL       ←
utm_term            text       NULL       ←
viewport_width      integer    NULL       ←
viewport_height     integer    NULL       ←
niche               text       NULL
ip                  inet       NULL
country             char(2)    NULL       ←
user_agent          text       NULL
browser             text       NULL
browser_version     text       NULL       ←
os                  text       NULL
device_type         text       NULL
event_id            uuid       NULL
event_type_id       uuid       NULL → FK event_types(id)
event_props         jsonb      NULL
```

### Despues (27 columnas)

```text
tracking_events (RANGE PARTITION BY created_at)
─────────────────────────────────────────────────
PK logico: (session_id, page_id, created_at)  ← sin cambio
─────────────────────────────────────────────────
session_id          text       NOT NULL
page_id             uuid       NOT NULL
created_at          timestamptz NOT NULL
received_at         timestamptz NOT NULL
expires_at          timestamptz NULL
[stream_event_id    DROP]                  ← columna eliminada
page_url            text       NULL       (Pydantic exige ''; Neon NULL aceptado por compat)
page_title          text       NULL
page_path           text       NULL
referrer            text       NULL
utm_source          text       NULL
utm_medium          text       NULL
utm_campaign        text       NULL
utm_content         text       NULL
utm_term            text       NULL
viewport_width      integer    NULL
viewport_height     integer    NULL
niche               text       NULL
ip                  inet       NULL
country             char(2)    NULL       (poblado via cloudfront-viewer-country)
user_agent          text       NULL
browser             text       NULL
browser_version     text       NULL
os                  text       NULL
device_type         text       NULL
event_id            uuid       NULL
event_type_id       uuid       NULL → FK event_types(id)
event_props         jsonb      NULL
```

> **Nota sobre NULL en Neon vs Pydantic**: la columna sigue `NULL`-tolerant
> a nivel DB para no romper compatibilidad con filas viejas ni con
> operaciones de batch backfill futuras. La obligatoriedad se enforce en la
> capa Pydantic del Lambda (rechaza con HTTP 400). Cambiar el constraint
> a `NOT NULL` requiere backfill previo + downtime breve y queda fuera de
> scope.

### Indices afectados

| Indice | Estado |
|--------|--------|
| `idx_tracking_session_created` | sin cambio |
| `idx_tracking_created_brin` | sin cambio |
| `idx_tracking_page_path` | sin cambio (poblado de verdad ahora) |
| `idx_tracking_referrer WHERE NOT NULL` | sin cambio |
| `idx_tracking_utm_source WHERE NOT NULL` | sin cambio |
| `idx_tracking_country WHERE NOT NULL` | sin cambio (poblado) |
| `idx_tracking_device_type` | sin cambio |
| `idx_tracking_niche_created` | sin cambio |
| `idx_tracking_event_type` | sin cambio |

Ningun indice menciona `stream_event_id`, asi que la migracion drop es
limpia.

---

¿Justifica `.mmd` permanente? **No**. Los dos diagramas son one-shot del
plan: una vez mergeado, viven en el git log. No se promueven a
`docs/diagrams/`.

---

Siguiente: [03. Tests requeridos →](03-tests-requeridos.md)
