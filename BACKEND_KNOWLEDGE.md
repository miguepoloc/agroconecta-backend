# AgroConecta — Conocimiento de negocio para el backend

> Documento de referencia para construir la API. Describe el dominio completo del proyecto: qué es, quiénes son los actores, qué reglas aplican y qué endpoints necesita el frontend existente.

---

## 1. ¿Qué es AgroConecta?

Marketplace B2B/B2C agrícola colombiano que conecta **agricultores** con **compradores individuales** e **instituciones** (colegios, hospitales, programas PAE). La propuesta de valor central es **trazabilidad** y **comercio justo**: el 82% de cada compra va directo al agricultor, todos los productos tienen número de lote con cadena de custodia pública.

### Principios de negocio

- Todo producto tiene un número de lote único (`LOT-YYYY-MMDD-XX`) con cadena de custodia pública (sin auth).
- Existen dos precios: precio individual y precio institucional (siempre menor).
- Los precios se pueden escalar por volumen (tabla de rangos de kg).
- El envío es gratis si el subtotal supera **COP 200.000**; si no, cuesta **COP 15.000**.
- Los agricultores deben tener certificaciones vigentes para poder vender. Si una certificación vence, el admin recibe alerta y puede suspender al agricultor.
- Las instituciones pueden emitir órdenes con número de orden de compra (PO number).

---

## 2. Actores y roles

| Rol | Cookie/token | Acceso |
|-----|-------------|--------|
| `comprador` | Autenticado o anónimo | Catálogo, producto, carrito, checkout, mis pedidos |
| `agricultor` | Autenticado | Panel propio: productos, órdenes, compliance, KPIs |
| `institucion` | Autenticado | Portal institucional: órdenes, licitaciones, KPIs |
| `admin` | Autenticado | Todo: gestión de pedidos, agricultores, métricas |

### Rutas protegidas (middleware actual)

```
/admin/*        → solo admin
/agricultor/*   → solo agricultor
/institucional  → institucion o admin
/carrito, /checkout, /pedido/* → cualquier rol autenticado (comprador puede comprar anónimo en MVP)
```

---

## 3. Modelos de datos

### 3.1 User

```ts
{
  id: string                  // UUID
  name: string
  email: string               // unique
  password: string            // bcrypt hash
  role: "comprador" | "agricultor" | "institucion" | "admin"
  avatar?: string             // URL
  phone?: string
  nit?: string                // solo institucion
  institutionName?: string    // solo institucion
  createdAt: datetime
  updatedAt: datetime
}
```

### 3.2 Farmer (perfil extendido del agricultor)

Un `User` con `role = "agricultor"` tiene asociado un perfil `Farmer`:

```ts
{
  id: string
  userId: string              // FK → User
  name: string
  avatar: string
  region: string              // ej. "Valle de Tenza"
  department: string          // departamento colombiano
  bio: string
  quote: string               // frase característica
  phone: string
  email: string
  totalSales: number          // COP, calculado
  activeProducts: number      // calculado
  joinedDate: date
  sustainabilityRank: "Bronze" | "Silver" | "Gold"  // calculado por ventas y certif.
  complianceStatus: "ACTIVE" | "RENEWAL_NEEDED" | "EXPIRED"  // derivado de certifications
}
```

**Regla de `complianceStatus`:**
- `ACTIVE` si todas las certificaciones están `ACTIVE`
- `RENEWAL_NEEDED` si al menos una certificación está `RENEWAL_NEEDED`
- `EXPIRED` si al menos una está `EXPIRED`

**Regla de `sustainabilityRank`:**
- `Gold`: ventas totales > COP 100M Y todas las certif. `ACTIVE`
- `Silver`: ventas totales > COP 50M O tiene al menos 2 certif. activas
- `Bronze`: resto

### 3.3 Certification

```ts
{
  id: string
  farmerId: string            // FK → Farmer
  type: "GlobalGAP" | "FairTrade" | "ICA" | "INVIMA" | "Orgánico"
  issueDate: date
  expiryDate: date
  status: "ACTIVE" | "RENEWAL_NEEDED" | "EXPIRED"
  documentUrl?: string        // URL al PDF del certificado
}
```

**Regla de `status` (calculado automáticamente):**
- `ACTIVE`: `expiryDate` > today + 60 días
- `RENEWAL_NEEDED`: `expiryDate` dentro de los próximos 60 días
- `EXPIRED`: `expiryDate` < today

### 3.4 Product

```ts
{
  id: string
  slug: string                // unique, URL-friendly, ej. "papa-criolla-boyaca"
  name: string
  category: "Verduras" | "Frutas" | "Granos" | "Tubérculos" | "Hierbas" | "Hortalizas" | "Lácteos"
  price: number               // COP/kg, precio individual base
  institutionalPrice?: number // COP/kg, precio para rol "institucion"
  minimumLot: number          // kg mínimo por compra
  unit: string                // "kg" en todos los casos actuales
  description: string
  images: string[]            // array de URLs
  farmerId: string            // FK → Farmer
  lotNumber: string           // unique, formato "LOT-YYYY-MMDD-XX"
  harvestDate: date
  freshnessScore: number      // 0–100, calculado: 100 - (days_since_harvest * 3)
  certifications: string[]    // subconjunto de los tipos del farmer
  inStock: boolean
  featured: boolean           // destacado en homepage
  weight?: number             // kg disponibles en stock
  createdAt: datetime
  updatedAt: datetime
}
```

**Regla de `freshnessScore`:**
- `freshnessScore = max(0, 100 - (diasDesdeCosecha * 3))`
- Se recalcula en cada consulta o con un job diario.

**Regla de `lotNumber`:**
- Formato: `LOT-{AÑO}-{MMDD}-{CÓDIGO2}`
- Debe ser único en todo el sistema.
- El código de 2 letras identifica el producto (PC = Papa Criolla, TC = Tomate Chonto, etc.)

### 3.5 VolumePrice (tabla de precios por volumen)

```ts
{
  id: string
  productId: string           // FK → Product
  minKg: number
  maxKg?: number              // null = sin límite superior
  pricePerKg: number          // COP
  label: string               // "Detalle" | "Mayorista" | "Institucional"
}
```

**Regla de precio activo:** dado `quantity` kg, se aplica el `VolumePrice` donde `minKg <= quantity <= maxKg` (o `maxKg` es null). Si no hay tabla de volumen, se usa `product.price`.

### 3.6 TraceabilityStep (cadena de custodia)

```ts
{
  id: string
  productId: string           // FK → Product
  stage: "cosecha" | "empaque" | "envio" | "llegada"
  date: date
  location: string
  responsible: string
  notes?: string
  order: number               // 1, 2, 3, 4 para ordenar
}
```

### 3.7 Order

```ts
{
  id: string
  orderNumber: string         // unique, formato "AGC-{AÑO}-{NNNNNN}"
  type: "individual" | "institucional"
  status: "pendiente" | "confirmado" | "en_camino" | "entregado" | "cancelado"
  userId: string              // FK → User (comprador o institución)
  subtotal: number            // COP
  deliveryFee: number         // 0 o 15000
  total: number               // subtotal + deliveryFee
  paymentMethod: "tarjeta" | "pse" | "nequi"
  deliveryDate: date
  createdAt: datetime
  updatedAt: datetime
  purchaseOrderNumber?: string // solo tipo "institucional"
  institutionId?: string       // solo tipo "institucional"

  // Dirección de entrega (embebida o tabla separada)
  deliveryStreet: string
  deliveryCity: string
  deliveryDepartment: string
  deliveryPostalCode?: string
  deliveryNotes?: string
}
```

**Regla de `orderNumber`:**
- Formato: `AGC-{AÑO}-{secuencial 5 dígitos}`, ej. `AGC-2026-00001`
- Autoincremental por año.

**Regla de `deliveryFee`:**
- `0` si `subtotal >= 200000`
- `15000` en caso contrario
- Las órdenes institucionales siempre tienen `deliveryFee = 0`

**Regla de `type`:**
- `"institucional"` si el `userId` pertenece a un usuario con `role = "institucion"`
- `"individual"` en los demás casos

**Transiciones de estado válidas:**
```
pendiente → confirmado → en_camino → entregado
pendiente → cancelado
confirmado → cancelado
```
Solo el `admin` puede cambiar el estado.

### 3.8 OrderItem

```ts
{
  id: string
  orderId: string             // FK → Order
  productId: string           // FK → Product
  quantity: number            // kg
  unitPrice: number           // COP/kg al momento de la compra (snapshot)
}
```

**Importante:** `unitPrice` es un snapshot del precio en el momento de la compra, no una referencia viva al producto. No cambiar si el producto cambia de precio.

---

## 4. Endpoints requeridos

La API debe seguir convenciones REST. Base: `/api/v1`.

### 4.1 Auth

| Método | Ruta | Body | Respuesta | Notas |
|--------|------|------|-----------|-------|
| `POST` | `/auth/login` | `{email, password}` | `{token, user}` | JWT o cookie httpOnly |
| `POST` | `/auth/logout` | — | `200` | Invalida sesión |
| `POST` | `/auth/register` | ver §4.1.1 | `{token, user}` | |
| `GET` | `/auth/me` | — | `{user}` | Requiere token |
| `POST` | `/auth/refresh` | `{refreshToken}` | `{token}` | Opcional |

#### 4.1.1 Register body por rol

```json
// comprador
{ "name": "", "email": "", "password": "", "phone": "", "role": "comprador" }

// agricultor
{ "name": "", "email": "", "password": "", "phone": "", "role": "agricultor",
  "region": "", "department": "", "bio": "" }

// institucion
{ "name": "", "email": "", "password": "", "phone": "", "role": "institucion",
  "nit": "", "institutionName": "", "institutionType": "" }
```

---

### 4.2 Products (catálogo público)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/products` | No | Listado con filtros |
| `GET` | `/products/:slug` | No | Detalle por slug |
| `GET` | `/products/lot/:lotNumber` | No | Detalle por número de lote (trazabilidad pública) |
| `GET` | `/products/featured` | No | Productos destacados (homepage) |

#### Query params de `/products`

```
?categoria=Verduras         // filtro por categoría
?cert=GlobalGAP             // filtro por certificación
?lote=50                    // minimumLot >= N
?orden=featured|price-asc|price-desc|freshness
?page=1&limit=20
```

#### Respuesta de `/products/:slug`

Incluir siempre: `farmer` (perfil completo del agricultor), `traceabilityChain[]`, `volumePrices[]`.

---

### 4.3 Farmers (perfiles públicos)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/farmers` | No | Lista de agricultores (para homepage: los Gold) |
| `GET` | `/farmers/:id` | No | Perfil público completo |
| `GET` | `/farmers/:id/products` | No | Productos de un agricultor |

---

### 4.4 Orders (pedidos)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `POST` | `/orders` | Sí (comprador, institucion) | Crear pedido desde checkout |
| `GET` | `/orders/me` | Sí | Mis pedidos (comprador/institucion) |
| `GET` | `/orders/:id` | Sí | Detalle de un pedido propio |

#### Body de `POST /orders`

```json
{
  "items": [
    { "productId": "...", "quantity": 5 }
  ],
  "paymentMethod": "tarjeta|pse|nequi",
  "deliveryDate": "2026-05-10",
  "deliveryAddress": {
    "street": "Cra 15 #85-20",
    "city": "Bogotá",
    "department": "Cundinamarca",
    "notes": "Piso 3"
  },
  "purchaseOrderNumber": "PO-2026-0318"  // opcional, solo institucion
}
```

**Reglas al crear pedido:**
1. Verificar que todos los productos existen y están `inStock: true`.
2. Verificar que `quantity >= product.minimumLot` por cada ítem.
3. Calcular `unitPrice` según tabla `VolumePrice` (o `price` base). Si el usuario es `institucion`, usar `institutionalPrice`.
4. Calcular `subtotal = Σ(unitPrice * quantity)`.
5. Calcular `deliveryFee`: 0 si `subtotal >= 200000` o si `user.role === "institucion"`, sino 15000.
6. Calcular `total = subtotal + deliveryFee`.
7. Generar `orderNumber` con formato `AGC-{AÑO}-{NNNNNN}`.
8. Establecer `status = "pendiente"`.
9. Establecer `type = "institucional"` si `user.role === "institucion"`, sino `"individual"`.

---

### 4.5 Admin — Pedidos

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/admin/orders` | admin | Lista todos los pedidos con filtros |
| `GET` | `/admin/orders/:id` | admin | Detalle de cualquier pedido |
| `PATCH` | `/admin/orders/:id/status` | admin | Cambiar estado del pedido |

#### Query params de `/admin/orders`

```
?search=AGC-2026|nombre_cliente
?status=pendiente|confirmado|en_camino|entregado|cancelado
?type=individual|institucional
?page=1&limit=20
```

#### Body de `PATCH /admin/orders/:id/status`

```json
{ "status": "confirmado" }
```

**Validar transición válida** (ver §3.7).

---

### 4.6 Admin — Agricultores

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/admin/farmers` | admin | Lista agricultores con filtros |
| `GET` | `/admin/farmers/:id` | admin | Perfil completo + sus productos + resumen financiero |
| `PATCH` | `/admin/farmers/:id/suspend` | admin | Suspender agricultor |
| `PATCH` | `/admin/farmers/:id/reactivate` | admin | Reactivar agricultor |

#### Query params de `/admin/farmers`

```
?search=nombre
?compliance=ACTIVE|RENEWAL_NEEDED|EXPIRED
?rank=Gold|Silver|Bronze
```

**Al suspender:** el agricultor y todos sus productos quedan fuera del catálogo público (`inStock = false`, visible en admin pero no en `/products`).

---

### 4.7 Admin — KPIs y métricas (dashboard)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/admin/metrics` | admin | KPIs globales |
| `GET` | `/admin/metrics/sales-chart` | admin | Datos del gráfico de ventas por período |

#### Respuesta de `/admin/metrics`

```json
{
  "totalOrders": 1234,
  "totalRevenue": 58340000,
  "activeFarmers": 47,
  "pendingOrders": 12,
  "ordersThisMonth": 89,
  "revenueThisMonth": 12500000
}
```

#### Respuesta de `/admin/metrics/sales-chart`

```json
{
  "labels": ["Ene", "Feb", "Mar", "Abr", "May"],
  "values": [38000000, 52000000, 61000000, 47000000, 78000000]
}
```

---

### 4.8 Agricultor — Panel propio

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/farmer/me` | agricultor | Perfil propio con certifications y KPIs |
| `GET` | `/farmer/me/products` | agricultor | Mis productos |
| `GET` | `/farmer/me/orders` | agricultor | Órdenes que incluyen mis productos |

#### Respuesta de `/farmer/me`

```json
{
  "farmer": { ...perfil },
  "certifications": [ ...array ],
  "kpis": {
    "totalSales": 128500000,
    "activeProducts": 5,
    "pendingOrders": 2,
    "sustainabilityRank": "Gold",
    "complianceStatus": "RENEWAL_NEEDED"
  }
}
```

---

### 4.9 Institucional — Portal

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/institution/me/orders` | institucion | Mis órdenes institucionales |
| `GET` | `/institution/me/metrics` | institucion | KPIs del portal institucional |

#### Respuesta de `/institution/me/metrics`

```json
{
  "activeOrders": 3,
  "totalInvested": 4820000,
  "availableProducts": 47,
  "activeLicitaciones": 2
}
```

---

### 4.10 Trazabilidad pública

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/traceability/:lotNumber` | No | Info completa de un lote (pública) |

#### Respuesta de `/traceability/:lotNumber`

```json
{
  "product": {
    "id": "...",
    "name": "Papa Criolla Boyacá",
    "lotNumber": "LOT-2026-0501-PC",
    "harvestDate": "2026-05-01",
    "freshnessScore": 97,
    "certifications": ["GlobalGAP"],
    "category": "Tubérculos"
  },
  "farmer": {
    "name": "Carlos Muñoz",
    "region": "Valle de Tenza",
    "department": "Boyacá",
    "certifications": [ ...array ]
  },
  "traceabilityChain": [
    { "stage": "cosecha", "date": "...", "location": "...", "responsible": "...", "notes": "..." },
    { "stage": "empaque", ... },
    { "stage": "envio", ... },
    { "stage": "llegada", ... }
  ]
}
```

---

### 4.11 Agricultor — Gestión de productos (CRUD futuro)

Estos endpoints no existen aún en el frontend pero son necesarios para el flujo completo:

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `POST` | `/farmer/me/products` | agricultor | Crear producto |
| `PUT` | `/farmer/me/products/:id` | agricultor | Actualizar producto |
| `DELETE` | `/farmer/me/products/:id` | agricultor | Eliminar producto |
| `PATCH` | `/farmer/me/products/:id/stock` | agricultor | Actualizar `inStock` y `weight` |

---

## 5. Reglas de negocio completas

### 5.1 Autenticación

- JWT con expiración de 24h (`access_token`) + refresh token de 7 días.
- El frontend guarda el rol en una cookie `agro_auth_role` para el middleware Edge de Next.js. La API debe emitir esta cookie (httpOnly: false, path=/, SameSite=Strict) o el frontend la escribe al recibir el token.
- Al login, la respuesta incluye `{ token, refreshToken, user: { id, name, email, role, avatar } }`.

### 5.2 Precios

- El precio que se aplica a un comprador individual es `product.price` (o el rango de `volumePrices` que corresponda a la cantidad).
- El precio que se aplica a una institución es `product.institutionalPrice` (o el rango de `volumePrices` con `label: "Institucional"`).
- Si no hay tabla de volumen, el precio es siempre `product.price` / `product.institutionalPrice`.
- El `unitPrice` en `OrderItem` es el precio real cobrado al momento de la compra.

### 5.3 Catálogo y visibilidad

- Un producto es visible públicamente si: `inStock = true` Y el agricultor dueño no está suspendido.
- El admin puede ver todos los productos sin importar estado.
- El agricultor solo ve sus propios productos.
- El filtro de lote mínimo en el catálogo filtra productos donde `minimumLot >= N` (el frontend lo aplica como "quiero comprar al menos N kg").

### 5.4 Frescura

- `freshnessScore = max(0, 100 - (diasDesdeCosecha × 3))`
- Un producto con 0% de frescura debe marcarse `inStock = false` automáticamente (job diario).
- La pantalla de detalle de producto muestra la frescura en tiempo real.

### 5.5 Certificaciones y compliance

- Un agricultor con `complianceStatus = "EXPIRED"` no puede tener productos en el catálogo.
- Un agricultor con `complianceStatus = "RENEWAL_NEEDED"` puede seguir vendiendo pero el admin recibe alerta.
- La pantalla `/admin/agricultores/:id` muestra un banner de alerta con las certificaciones por renovar.
- El panel del agricultor (`/agricultor/panel`) muestra el mismo estado y un toast de warning si hay renovaciones pendientes.
- El backend debe tener un job que cada día recalcula `complianceStatus` de todos los agricultores.

### 5.6 Número de orden y lote

- `orderNumber` formato: `AGC-{AÑO}-{NNNNNN}` — secuencial dentro del año, con ceros a la izquierda.
- `lotNumber` formato: `LOT-{YYYY}-{MMDD}-{XX}` — XX es un código de 2 letras del producto.
- Ambos son únicos e inmutables una vez creados.

### 5.7 Flujo de checkout

El frontend manda un solo `POST /orders` al confirmar el pago (paso 2). El backend debe:
1. Validar stock y cantidad mínima.
2. Calcular precios (ver §5.2).
3. Procesar el pago (integración con PSE/Wompi/Nequi — en MVP puede ser mock).
4. Crear la orden con estado `"pendiente"`.
5. Devolver `{ orderNumber, total, estimatedDelivery }`.
6. Enviar email de confirmación al comprador (en MVP puede ser log).

### 5.8 Órdenes institucionales

- Requieren `purchaseOrderNumber` (número de orden de compra interna de la institución).
- `deliveryFee = 0` siempre.
- Pueden tener montos mayores (órdenes de COP 1M+ son normales).
- El portal institucional muestra un listado de licitaciones activas (en MVP son estáticas; en producción vendrían de una tabla `Licitacion`).

### 5.9 Impacto social

- El frontend muestra "82% va directo al agricultor". El backend puede exponer un endpoint `/metrics/impact` con datos calculados.
- `farmerRevenuePct = 0.82` es un parámetro de negocio configurable.

---

## 6. Estructura de rutas del frontend → endpoints necesarios

| Ruta frontend | Endpoint(s) que consume |
|--------------|------------------------|
| `/` (homepage) | `GET /products/featured`, `GET /farmers?rank=Gold` |
| `/catalogo` | `GET /products?...filtros` |
| `/productos/:slug` | `GET /products/:slug` (incluye farmer + traceability + volumePrices) |
| `/carrito` | Solo estado local (localStorage) |
| `/checkout` | `POST /orders` |
| `/pedido/confirmacion` | Resultado del `POST /orders` |
| `/login` | `POST /auth/login` |
| `/registro` | `POST /auth/register` |
| `/lote/:id` | `GET /traceability/:lotNumber` |
| `/institucional` | `GET /institution/me/orders`, `GET /institution/me/metrics` |
| `/agricultor/panel` | `GET /farmer/me`, `GET /farmer/me/orders`, `GET /farmer/me/products` |
| `/admin` | `GET /admin/metrics`, `GET /admin/metrics/sales-chart`, `GET /admin/orders?limit=5` |
| `/admin/pedidos` | `GET /admin/orders?...filtros` |
| `/admin/pedidos/:id` | `GET /admin/orders/:id`, `PATCH /admin/orders/:id/status` |
| `/admin/agricultores` | `GET /admin/farmers?...filtros` |
| `/admin/agricultores/:id` | `GET /admin/farmers/:id`, `PATCH /admin/farmers/:id/suspend` |

---

## 7. Campos de respuesta esperados por el frontend

El frontend espera estos shapes exactos (los nombres vienen del código TypeScript en `src/lib/types.ts`):

### User (en JWT payload y respuesta de `/auth/me`)

```json
{ "id": "", "name": "", "email": "", "role": "", "avatar": "", "phone": "", "nit": "", "institutionName": "" }
```

### Product (listado)

```json
{
  "id": "", "slug": "", "name": "", "category": "", "price": 0, "institutionalPrice": 0,
  "minimumLot": 0, "unit": "kg", "images": [], "farmerId": "", "lotNumber": "",
  "harvestDate": "", "freshnessScore": 0, "certifications": [], "inStock": true, "featured": false
}
```

### Product (detalle — incluye relaciones)

```json
{
  ...campos de listado,
  "description": "",
  "farmer": { ...Farmer completo },
  "traceabilityChain": [ { "stage": "", "date": "", "location": "", "responsible": "", "notes": "" } ],
  "volumePrices": [ { "minKg": 0, "maxKg": null, "pricePerKg": 0, "label": "" } ]
}
```

### Farmer (perfil completo)

```json
{
  "id": "", "name": "", "avatar": "", "region": "", "department": "", "bio": "", "quote": "",
  "certifications": [ { "type": "", "issueDate": "", "expiryDate": "", "status": "", "documentUrl": "" } ],
  "sustainabilityRank": "Gold", "complianceStatus": "ACTIVE",
  "totalSales": 0, "activeProducts": 0, "joinedDate": "", "phone": "", "email": ""
}
```

### Order (listado y detalle)

```json
{
  "id": "", "orderNumber": "AGC-2026-00001", "type": "individual", "status": "pendiente",
  "userId": "", "user": { ...User básico },
  "items": [ { "productId": "", "product": { ...Product }, "quantity": 0, "unitPrice": 0 } ],
  "subtotal": 0, "deliveryFee": 0, "total": 0,
  "paymentMethod": "tarjeta", "deliveryDate": "", "createdAt": "",
  "deliveryAddress": { "street": "", "city": "", "department": "", "notes": "" },
  "purchaseOrderNumber": "", "institutionId": ""
}
```

---

## 8. Esquema de base de datos (PostgreSQL)

> El esquema usa PostgreSQL con UUIDs como PK. Se incluyen constraints, índices y relaciones. Las columnas calculadas (`freshnessScore`, `complianceStatus`, `sustainabilityRank`) se pueden almacenar desnormalizadas y recalcular con jobs, o calcularse en tiempo de consulta con funciones.

---

### 8.1 Diagrama de relaciones

```
users ──────────────── farmers (1:1)
  │                        │
  │                        ├── certifications (1:N)
  │                        └── products (1:N)
  │                                │
  │                                ├── volume_prices (1:N)
  │                                └── traceability_steps (1:N)
  │
  └── orders (1:N)
          │
          └── order_items (1:N) ──── products (N:1)
```

---

### 8.2 Tabla: `users`

```sql
CREATE TABLE users (
  id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  name              VARCHAR(150)  NOT NULL,
  email             VARCHAR(254)  NOT NULL UNIQUE,
  password_hash     VARCHAR(255)  NOT NULL,                   -- bcrypt
  role              VARCHAR(20)   NOT NULL CHECK (role IN ('comprador', 'agricultor', 'institucion', 'admin')),
  avatar_url        TEXT,
  phone             VARCHAR(20),
  nit               VARCHAR(20),                              -- solo role='institucion'
  institution_name  VARCHAR(200),                             -- solo role='institucion'
  institution_type  VARCHAR(100),                             -- 'colegio', 'hospital', 'entidad_publica'…
  is_active         BOOLEAN       NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role  ON users (role);
```

**Constraints de negocio:**

- `nit` y `institution_name` solo aplican cuando `role = 'institucion'` — validar en capa de aplicación.
- `is_active = false` bloquea el login sin eliminar el registro.

---

### 8.3 Tabla: `farmers`

```sql
CREATE TABLE farmers (
  id                 UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id            UUID          NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  region             VARCHAR(100)  NOT NULL,                  -- ej. "Valle de Tenza"
  department         VARCHAR(100)  NOT NULL,                  -- departamento colombiano
  bio                TEXT,
  quote              TEXT,
  phone              VARCHAR(20),
  email              VARCHAR(254),
  total_sales        BIGINT        NOT NULL DEFAULT 0,        -- COP, actualizado por job
  active_products    INT           NOT NULL DEFAULT 0,        -- actualizado por job/trigger
  joined_date        DATE          NOT NULL DEFAULT CURRENT_DATE,
  sustainability_rank VARCHAR(10)  NOT NULL DEFAULT 'Bronze'  -- 'Bronze' | 'Silver' | 'Gold'
                      CHECK (sustainability_rank IN ('Bronze', 'Silver', 'Gold')),
  compliance_status  VARCHAR(20)   NOT NULL DEFAULT 'ACTIVE'
                      CHECK (compliance_status IN ('ACTIVE', 'RENEWAL_NEEDED', 'EXPIRED')),
  is_suspended       BOOLEAN       NOT NULL DEFAULT FALSE,    -- suspendido por admin
  suspended_at       TIMESTAMPTZ,
  suspended_reason   TEXT,
  created_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_farmers_user_id          ON farmers (user_id);
CREATE INDEX idx_farmers_compliance       ON farmers (compliance_status);
CREATE INDEX idx_farmers_rank             ON farmers (sustainability_rank);
CREATE INDEX idx_farmers_is_suspended     ON farmers (is_suspended);
```

**Regla `compliance_status` (job diario o trigger en `certifications`):**

```sql
-- Pseudo-lógica del job:
UPDATE farmers f SET
  compliance_status = (
    CASE
      WHEN EXISTS (
        SELECT 1 FROM certifications c
        WHERE c.farmer_id = f.id AND c.expiry_date < NOW()
      ) THEN 'EXPIRED'
      WHEN EXISTS (
        SELECT 1 FROM certifications c
        WHERE c.farmer_id = f.id
          AND c.expiry_date BETWEEN NOW() AND NOW() + INTERVAL '60 days'
      ) THEN 'RENEWAL_NEEDED'
      ELSE 'ACTIVE'
    END
  );
```

**Regla `sustainability_rank` (job semanal):**

```sql
-- Gold: total_sales > 100_000_000 Y compliance_status = 'ACTIVE'
-- Silver: total_sales > 50_000_000 O tiene >= 2 certif. activas
-- Bronze: resto
```

---

### 8.4 Tabla: `certifications`

```sql
CREATE TABLE certifications (
  id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  farmer_id     UUID         NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
  type          VARCHAR(20)  NOT NULL
                CHECK (type IN ('GlobalGAP', 'FairTrade', 'ICA', 'INVIMA', 'Orgánico')),
  issue_date    DATE         NOT NULL,
  expiry_date   DATE         NOT NULL,
  status        VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE'
                CHECK (status IN ('ACTIVE', 'RENEWAL_NEEDED', 'EXPIRED')),
  document_url  TEXT,                                          -- URL al PDF
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_farmer_cert_type UNIQUE (farmer_id, type)     -- un tipo por agricultor
);

CREATE INDEX idx_certifications_farmer_id   ON certifications (farmer_id);
CREATE INDEX idx_certifications_expiry_date ON certifications (expiry_date);
CREATE INDEX idx_certifications_status      ON certifications (status);
```

**Regla `status` (calculada por job diario):**

```sql
UPDATE certifications SET
  status = CASE
    WHEN expiry_date < CURRENT_DATE THEN 'EXPIRED'
    WHEN expiry_date < CURRENT_DATE + INTERVAL '60 days' THEN 'RENEWAL_NEEDED'
    ELSE 'ACTIVE'
  END;
```

---

### 8.5 Tabla: `products`

```sql
CREATE TABLE products (
  id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  slug                VARCHAR(150)  NOT NULL UNIQUE,
  name                VARCHAR(200)  NOT NULL,
  category            VARCHAR(20)   NOT NULL
                      CHECK (category IN ('Verduras','Frutas','Granos','Tubérculos','Hierbas','Hortalizas','Lácteos')),
  price               INT           NOT NULL CHECK (price > 0),          -- COP/kg
  institutional_price INT           CHECK (institutional_price > 0),     -- COP/kg, nullable
  minimum_lot         INT           NOT NULL DEFAULT 1 CHECK (minimum_lot >= 1), -- kg
  unit                VARCHAR(10)   NOT NULL DEFAULT 'kg',
  description         TEXT,
  images              TEXT[]        NOT NULL DEFAULT '{}',                -- array de URLs
  farmer_id           UUID          NOT NULL REFERENCES farmers(id) ON DELETE RESTRICT,
  lot_number          VARCHAR(25)   NOT NULL UNIQUE,                     -- LOT-YYYY-MMDD-XX
  harvest_date        DATE          NOT NULL,
  freshness_score     SMALLINT      NOT NULL DEFAULT 100
                      CHECK (freshness_score BETWEEN 0 AND 100),         -- recalculado por job
  certifications      TEXT[]        NOT NULL DEFAULT '{}',               -- subconjunto de tipos
  in_stock            BOOLEAN       NOT NULL DEFAULT TRUE,
  featured            BOOLEAN       NOT NULL DEFAULT FALSE,
  weight_available    NUMERIC(10,2),                                     -- kg disponibles, nullable
  created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_farmer_id     ON products (farmer_id);
CREATE INDEX idx_products_category      ON products (category);
CREATE INDEX idx_products_in_stock      ON products (in_stock);
CREATE INDEX idx_products_featured      ON products (featured) WHERE featured = TRUE;
CREATE INDEX idx_products_lot_number    ON products (lot_number);
CREATE INDEX idx_products_freshness     ON products (freshness_score);
CREATE INDEX idx_products_slug          ON products (slug);

-- Índice para búsqueda de texto en nombre y descripción
CREATE INDEX idx_products_search ON products
  USING gin(to_tsvector('spanish', name || ' ' || COALESCE(description, '')));
```

**Regla `lot_number`:**

- Formato estricto: `LOT-{YYYY}-{MMDD}-{XX}` donde XX es 2 letras mayúsculas.
- Constraint a nivel de aplicación: `CHECK (lot_number ~ '^LOT-\d{4}-\d{4}-[A-Z]{2}$')`.

**Regla `freshness_score` (job diario):**

```sql
UPDATE products SET
  freshness_score = GREATEST(0, 100 - (CURRENT_DATE - harvest_date) * 3),
  in_stock = CASE
    WHEN GREATEST(0, 100 - (CURRENT_DATE - harvest_date) * 3) = 0 THEN FALSE
    ELSE in_stock
  END;
```

**Visibilidad pública:** un producto es visible si `in_stock = TRUE` AND el farmer asociado tiene `is_suspended = FALSE` AND `compliance_status != 'EXPIRED'`.

---

### 8.6 Tabla: `volume_prices`

```sql
CREATE TABLE volume_prices (
  id           UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id   UUID          NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  min_kg       INT           NOT NULL CHECK (min_kg >= 0),
  max_kg       INT           CHECK (max_kg > min_kg),                    -- NULL = sin límite superior
  price_per_kg INT           NOT NULL CHECK (price_per_kg > 0),          -- COP
  label        VARCHAR(50)   NOT NULL,                                   -- "Detalle", "Mayorista", "Institucional"
  created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_product_volume_min UNIQUE (product_id, min_kg)
);

CREATE INDEX idx_volume_prices_product_id ON volume_prices (product_id);
```

**Regla de precio activo (consulta):**

```sql
SELECT price_per_kg FROM volume_prices
WHERE product_id = $1
  AND min_kg <= $quantity
  AND (max_kg IS NULL OR max_kg >= $quantity)
ORDER BY min_kg DESC
LIMIT 1;
-- Si no hay resultado, usar products.price (o products.institutional_price para instituciones)
```

---

### 8.7 Tabla: `traceability_steps`

```sql
CREATE TABLE traceability_steps (
  id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id  UUID         NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  stage       VARCHAR(10)  NOT NULL
              CHECK (stage IN ('cosecha', 'empaque', 'envio', 'llegada')),
  step_order  SMALLINT     NOT NULL CHECK (step_order BETWEEN 1 AND 4),
  date        DATE         NOT NULL,
  location    TEXT         NOT NULL,
  responsible TEXT         NOT NULL,
  notes       TEXT,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

  CONSTRAINT uq_product_stage UNIQUE (product_id, stage)
);

CREATE INDEX idx_traceability_product_id ON traceability_steps (product_id);
```

**Orden estándar de stages:**

| `step_order` | `stage`  |
|--------------|----------|
| 1            | cosecha  |
| 2            | empaque  |
| 3            | envio    |
| 4            | llegada  |

---

### 8.8 Tabla: `orders`

```sql
CREATE TABLE orders (
  id                      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  order_number            VARCHAR(20)   NOT NULL UNIQUE,      -- AGC-{YYYY}-{NNNNNN}
  type                    VARCHAR(15)   NOT NULL
                          CHECK (type IN ('individual', 'institucional')),
  status                  VARCHAR(15)   NOT NULL DEFAULT 'pendiente'
                          CHECK (status IN ('pendiente','confirmado','en_camino','entregado','cancelado')),
  user_id                 UUID          NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  subtotal                INT           NOT NULL CHECK (subtotal >= 0),   -- COP
  delivery_fee            INT           NOT NULL DEFAULT 0 CHECK (delivery_fee >= 0), -- COP
  total                   INT           NOT NULL CHECK (total >= 0),      -- COP
  payment_method          VARCHAR(15)   NOT NULL
                          CHECK (payment_method IN ('tarjeta', 'pse', 'nequi')),
  delivery_date           DATE          NOT NULL,
  delivery_street         TEXT          NOT NULL,
  delivery_city           VARCHAR(100)  NOT NULL,
  delivery_department     VARCHAR(100)  NOT NULL,
  delivery_postal_code    VARCHAR(10),
  delivery_notes          TEXT,
  purchase_order_number   VARCHAR(50),                        -- PO number, solo institucional
  institution_id          UUID          REFERENCES users(id), -- FK al usuario institución
  payment_reference       VARCHAR(100),                       -- ref. del procesador de pagos
  cancelled_reason        TEXT,
  created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_user_id      ON orders (user_id);
CREATE INDEX idx_orders_status       ON orders (status);
CREATE INDEX idx_orders_type         ON orders (type);
CREATE INDEX idx_orders_created_at   ON orders (created_at DESC);
CREATE INDEX idx_orders_order_number ON orders (order_number);
CREATE INDEX idx_orders_institution  ON orders (institution_id) WHERE institution_id IS NOT NULL;

-- Secuencia para order_number por año
CREATE SEQUENCE order_number_seq START 1;
```

**Generación de `order_number`:**

```sql
-- En la aplicación al crear la orden:
-- order_number = 'AGC-' || EXTRACT(YEAR FROM NOW()) || '-' || LPAD(nextval('order_number_seq')::text, 5, '0')
-- Nota: reiniciar la secuencia cada año con un job (1 de enero)
```

**Transiciones de estado válidas (enforced en capa de aplicación):**
```
pendiente   → confirmado, cancelado
confirmado  → en_camino, cancelado
en_camino   → entregado
entregado   → (final)
cancelado   → (final)
```

**Regla `delivery_fee`:**

- `0` si `user.role = 'institucion'` O si `subtotal >= 200000`
- `15000` en todos los demás casos

---

### 8.9 Tabla: `order_items`

```sql
CREATE TABLE order_items (
  id          UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id    UUID          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id  UUID          NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
  quantity    NUMERIC(10,2) NOT NULL CHECK (quantity > 0),    -- kg
  unit_price  INT           NOT NULL CHECK (unit_price > 0),  -- COP/kg — snapshot inmutable
  created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_order_items_order_id   ON order_items (order_id);
CREATE INDEX idx_order_items_product_id ON order_items (product_id);
```

**Importante:** `unit_price` es el precio real cobrado al momento de la compra. Nunca se actualiza aunque el producto cambie de precio. Es el registro histórico del precio pagado.

---

### 8.10 Tabla: `refresh_tokens` (si se implementa refresh JWT)

```sql
CREATE TABLE refresh_tokens (
  id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash  VARCHAR(255) NOT NULL UNIQUE,                   -- hash del refresh token
  expires_at  TIMESTAMPTZ  NOT NULL,
  revoked     BOOLEAN      NOT NULL DEFAULT FALSE,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user_id    ON refresh_tokens (user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens (expires_at);
```

---

### 8.11 Vista útil: `products_public`

Vista para el catálogo público — filtra productos visibles con JOIN al farmer:

```sql
CREATE VIEW products_public AS
SELECT
  p.*,
  f.id          AS farmer_db_id,
  f.region      AS farmer_region,
  f.department  AS farmer_department,
  f.sustainability_rank AS farmer_rank,
  f.compliance_status   AS farmer_compliance,
  f.is_suspended        AS farmer_suspended
FROM products p
JOIN farmers f ON f.id = p.farmer_id
WHERE
  p.in_stock = TRUE
  AND f.is_suspended = FALSE
  AND f.compliance_status != 'EXPIRED';
```

---

### 8.12 Vista útil: `order_summary`

Para el dashboard de admin:

```sql
CREATE VIEW order_summary AS
SELECT
  o.id,
  o.order_number,
  o.type,
  o.status,
  o.total,
  o.created_at,
  u.name   AS user_name,
  u.email  AS user_email,
  u.role   AS user_role,
  COUNT(oi.id) AS item_count
FROM orders o
JOIN users u  ON u.id = o.user_id
JOIN order_items oi ON oi.order_id = o.id
GROUP BY o.id, u.id;
```

---

### 8.13 Resumen de tablas y relaciones

```
┌─────────────────────────────────────────────────────────────┐
│                        TABLAS                               │
├──────────────────────┬──────────────────────────────────────┤
│ users                │ PK: id (UUID)                        │
│ farmers              │ PK: id, FK: user_id → users          │
│ certifications       │ PK: id, FK: farmer_id → farmers      │
│ products             │ PK: id, FK: farmer_id → farmers      │
│ volume_prices        │ PK: id, FK: product_id → products    │
│ traceability_steps   │ PK: id, FK: product_id → products    │
│ orders               │ PK: id, FK: user_id → users          │
│ order_items          │ PK: id, FK: order_id, product_id     │
│ refresh_tokens       │ PK: id, FK: user_id → users          │
└──────────────────────┴──────────────────────────────────────┘

Columnas calculadas (no derivadas de relaciones):
  farmers.compliance_status     ← job diario sobre certifications.expiry_date
  farmers.sustainability_rank   ← job semanal sobre total_sales + certifications
  farmers.total_sales           ← trigger/job al crear orders
  farmers.active_products       ← trigger/job al crear/actualizar products
  products.freshness_score      ← job diario: 100 - (today - harvest_date) * 3
  certifications.status         ← job diario sobre expiry_date
```

---

## 8. Consideraciones de implementación

### 8.1 Stack sugerido

No está definido aún. Opciones compatibles con el frontend Next.js 16:

- **Node.js**: Express + Prisma + PostgreSQL (más rápido de iterar)
- **Node.js**: NestJS + TypeORM + PostgreSQL (más estructurado, mejor para escalar)
- **Python**: FastAPI + SQLAlchemy + PostgreSQL (si el equipo prefiere Python)
- **Go**: Gin + GORM + PostgreSQL (si se prioriza performance)

### 8.2 Base de datos

PostgreSQL recomendado. Tablas principales:

```
users, farmers, certifications, products, volume_prices, traceability_steps, orders, order_items
```

### 8.3 CORS

El frontend corre en `http://localhost:3000` (dev) y en el dominio de Vercel (prod). Configurar CORS apropiadamente.

### 8.4 Variables de entorno del frontend

El frontend ya tiene soporte para:
```
NEXT_PUBLIC_APP_NAME=AgroConecta
NEXT_PUBLIC_APP_ENV=development
```

Agregar:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1   # URL de la API
```

### 8.5 Jobs recurrentes necesarios

| Job | Frecuencia | Qué hace |
|-----|-----------|----------|
| `recalculate-freshness` | Diario (00:00) | Actualiza `freshnessScore` de todos los productos activos; marca `inStock = false` si freshnessScore = 0 |
| `recalculate-compliance` | Diario (00:00) | Recalcula `status` de todas las `Certification` según `expiryDate`; actualiza `complianceStatus` del Farmer |
| `recalculate-ranks` | Semanal | Recalcula `sustainabilityRank` de todos los agricultores |

### 8.6 Autenticación en producción

- El frontend usa una cookie `agro_auth_role` (sin httpOnly, `path=/`, `SameSite=Strict`) para que el middleware Edge de Next.js pueda leerla y proteger rutas sin hacer una llamada a la API.
- El `access_token` JWT se usa para todas las llamadas a la API.
- En producción, el `access_token` debería estar en una cookie httpOnly separada o en memoria (no localStorage) para mayor seguridad.

---

## 9. Datos de prueba (seed mínimo)

Para que el frontend funcione completo desde el primer día:

**4 usuarios:**
- `comprador@demo.co` / `demo123` — rol comprador
- `agricultor@demo.co` / `demo123` — rol agricultor (linked a Carlos Muñoz)
- `institucion@demo.co` / `demo123` — rol institucion (Colegio Distrital Los Pinos, NIT 900.123.456-7)
- `admin@demo.co` / `demo123` — rol admin

**4 agricultores:** Carlos Muñoz (Boyacá), María Ospina (Antioquia), Jesús Hernández (Cundinamarca), Ana Lucía Ramírez (Risaralda)

**8 productos:** papa criolla, tomate chonto, aguacate hass, espinaca hidropónica, zanahoria baby, maracuyá orgánico, fríjol cargamanto, pimentón rojo

**4 órdenes:** en estados variados (entregado, en_camino, confirmado, pendiente)

Los datos exactos están en `src/lib/mock-data.ts` del frontend.

---

## 10. Resumen de endpoints — listado rápido

```
# Auth
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/register
GET    /api/v1/auth/me
POST   /api/v1/auth/refresh

# Catálogo público (sin auth)
GET    /api/v1/products
GET    /api/v1/products/:slug
GET    /api/v1/products/lot/:lotNumber
GET    /api/v1/products/featured
GET    /api/v1/farmers
GET    /api/v1/farmers/:id
GET    /api/v1/farmers/:id/products
GET    /api/v1/traceability/:lotNumber

# Comprador / Institución
POST   /api/v1/orders
GET    /api/v1/orders/me
GET    /api/v1/orders/:id

# Agricultor (propio)
GET    /api/v1/farmer/me
GET    /api/v1/farmer/me/products
GET    /api/v1/farmer/me/orders
POST   /api/v1/farmer/me/products
PUT    /api/v1/farmer/me/products/:id
DELETE /api/v1/farmer/me/products/:id
PATCH  /api/v1/farmer/me/products/:id/stock

# Institucional
GET    /api/v1/institution/me/orders
GET    /api/v1/institution/me/metrics

# Admin — pedidos
GET    /api/v1/admin/orders
GET    /api/v1/admin/orders/:id
PATCH  /api/v1/admin/orders/:id/status

# Admin — agricultores
GET    /api/v1/admin/farmers
GET    /api/v1/admin/farmers/:id
PATCH  /api/v1/admin/farmers/:id/suspend
PATCH  /api/v1/admin/farmers/:id/reactivate

# Admin — métricas
GET    /api/v1/admin/metrics
GET    /api/v1/admin/metrics/sales-chart
```

Total: **~30 endpoints**
