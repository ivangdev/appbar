# 📋 Especificación POS Bar — Documento de Requisitos

> Versión para cliente.  
> *Basado en [`specs/PDR.yaml`](./specs/PDR.yaml) (spec técnica).*

---

## 🏷️ 1. Nombre del Proyecto
**POS Bar Digital** — Sistema web para el manejo de mesas, órdenes y pagos de un bar.

---

## 🎯 2. Visión

> Una aplicación web simple y rápida que permite al mesero tomar órdenes en
> tiempo real, cerrar cuentas y registrar pagos. El administrador controla
> catálogo de productos, mesas y ve reportes de ventas del día.

- **Plataforma**: Web (accesible desde cualquier navegador).
- **Login obligatorio** para admin y meseros.
- **Sin IVA / sin descuentos** (simplicidad operativa del bar).
- **Preparado para futuro** control de stock (no incluido en esta fase).
- **Sin impresión física** — todo se registra en la app.
- **Pagos parciales** — el mesero cobra acumulando abonos hasta cerrar la cuenta.

---

## 👥 3. Usuarios

| Rol | Qué puede hacer | Icono |
|---|---|---|
| **Administrador** | Gestionar usuarios, categorías, productos, mesas y reportes. | 👑 |
| **Mesero** | Abrir/cerrar órdenes, agregar productos, cobrar abonos, ver corte del día. | 🤝 |

---

## 🧭 4. Flujo de Trabajo (Mesero)

### Paso 1 — Ver mesas
- Lista en vivo de todas las mesas con su estado:
  - 🟢 Libre
  - 🔴 Ocupada
  - 🟡 Pagando

### Paso 2 — Abrir orden
- Clic en mesa **Libre** → se crea una orden.
- La mesa pasa a estado **Ocupada**.

### Paso 3 — Agregar productos
- Se despliega un menú agrupado por categorías (ej: Cervezas, Cócteles, Bocadillos).
- El mesero selecciona productos y cantidades.
- El **subtotal se actualiza automáticamente** mientras agrega/edita.

### Paso 4 — Cerrar la orden
- Al cerrar, se muestra el **total a pagar**.
- La mesa pasa a estado **Pagando**.

### Paso 5 — Cobrar (abonos parciales)
- El mesero registra un abono ingresando monto + método:
  - 💵 Efectivo
  - 📱 Nequi / Daviplata / Transferencia
  - Ej: "3 poker", "yo invito a Juan".

- El abono se **acumula** (pago parcial):
  - Mientras no cubre el total → orden **Parcialmente pagada**, mesa sigue **Pagando**.
  - Cuando la suma cubre el total → orden **Pagada**, mesa vuelve a **Libre**.

- **Cancelar abono**: el mesero puede anular un abono.
  - Si quedan abonos pendientes → sigue en **Pagando**.
  - Si se cancela todo → mesa vuelve a **Ocupada** (se pueden seguir pidiendo cosas).

---

## 🛠️ 5. Funcionalidades del Administrador

| Módulo | Acción | Detalle |
|---|---|---|
| 🔐 Login | Ingresar credenciales | Email + password |
| 👤 Meseros | Agregar / Editar / Desactivar | Nombre, email, password, rol |
| 📦 Categorías | Crear / Editar / Eliminar | Nombre, orden en menú |
| 🛒 Productos | Crear / Editar / Eliminar | Nombre, categoría, precio, costo, SKU |
| 🪑 Mesas | Crear / Editar / Eliminar | Número, etiqueta (opcional) |
| 📊 Reportes | Ver corte del día | Total vendido, por mesa, por producto _(meseros: solo lectura)_ |

---

## 📊 6. Reporte de Cierre del Día

Al final del día, admin y meseros abren el reporte y ven:

- **Total vendido del día** (solo órdenes pagadas).
- **Venta por mesa**.
- **Venta por producto** (cantidad + ingresos).

Ejemplo visual:

```
📅 11/10/2026
📈 Total del día: $1.850.000

🪑 Mesa 1 — $420.000
🪑 Mesa 2 — $380.000
🪑 Mesa 4 — $1.050.000

🛒 Top productos:
  - Cerveza — 42 uds — $840.000
  - Mojito — 28 uds — $700.000
```

---

## 🔒 7. Seguridad

| Aspecto | Detalle |
|---|---|
| Login | Usuario + contraseña (admin y meseros) |
| Contraseñas | Encriptadas (Argon2id) |
| Sesión | Token seguro, caduca y se cierra al salir |
| Permisos | Admin ve todo; mesero solo operativo |
| HTTPS | Comunicación encriptada (Caddy + certificado) |
| Datos | Copias de seguridad automáticas |

---

## ⚙️ 8. Requisitos Técnicos (Resumen)

| Requisito | Detalle |
|---|---|
| Dispositivos | Tabletas / PCs / celulares (navegador moderno) |
| Conexión | Acceso al VPS por internet (HTTPS) |
| Rendimiento | Soporte para varios meseros abiertos al mismo tiempo |
| Disponibilidad | Funciona sin internet (modo local) — *futuro* |

---

## 🗺️ 9. Roadmap (Fases)

| Fase | Qué incluye |
|---|---|
| **MVP (actual)** | Login, mesas, órdenes, abonos parciales, corte del día |
| **F1** | Control de inventario (stock, recetas) |
| **F2** | Pantalla de cocina / preparación |
| **F3** | Propinas, anulaciones con permiso |

---

## ✅ 10. Alcance (Lo que incluye / no incluye)

### Incluye
- Gestión de mesas en tiempo real.
- Órdenes con subtotal automático.
- Pagos parciales acumulables (efectivo / Nequi / transferencia).
- Cancelación de abonos parciales (mesa vuelve a "Ocupada").
- Corte del día (para admin y meseros).
- Login para admin y meseros.

### No incluye (ahora)
- Impuestos (IVA).
- Descuentos.
- Control de stock.
- No se imprimen recibos físicos.

---

## 📂 11. Archivos del Proyecto

| Archivo | Propósito |
|---|---|
| `docs/CLIENT_SPEC.md` | Este documento (para cliente) |
| `specs/PDR.yaml` | Especificación técnica maestra |
| `specs/openapi.yaml` | (Próximo) Spec API REST |
| `AGENTS.md` | (Próximo) Convenciones del repo |

---

¿Listo? Con esto el cliente entiende el sistema, funcionalidades y seguridad sin detalles técnicos.
