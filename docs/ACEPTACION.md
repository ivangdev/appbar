# Checklist de aceptación — POS Bar v1.0.0

Para firmar la entrega. Cada paso se ejecuta en el entorno final (VPS) con un
usuario admin y otro mesero. Marcar ✅ o ❌ y anotar observaciones.

## 1. Acceso y seguridad

| # | Prueba | Resultado esperado | ✅/❌ |
|---|---|---|---|
| 1.1 | Abrir `https://<dominio>` | Pantalla de login, sin advertencias de certificado | |
| 1.2 | Login con admin y con mesero | Redirige a `/tables`, menú según rol | |
| 1.3 | Cerrar sesión y volver a abrir `/tables` | Redirige a `/login` (cookie HttpOnly) | |
| 1.4 | Verificar `/health/ready` | `{"status":"ready"}` | |
| 1.5 | Intentar `http://<dominio>:8000` y `:5432` | Conexión rechazada (puertos no públicos) | |

## 2. Operación del mesero

| # | Prueba | Resultado esperado | ✅/❌ |
|---|---|---|---|
| 2.1 | Abrir una mesa libre | Mesa pasa a **Ocupada** y se crea orden `open` | |
| 2.2 | Agregar 2 productos con cantidades y nota | Subtotal correcto; nota visible | |
| 2.3 | Borrar la nota de un ítem | La nota desaparece (no reaparece al recargar) | |
| 2.4 | Cerrar la orden | Estado `closed`, mesa sigue ocupada | |
| 2.5 | Pagar 1 unidad de un ítem | `partially_paid`, mesa ocupada, "Pagado" parcial | |
| 2.6 | Anular ese abono | Vuelve a `closed`, queda registro de quién y cuándo | |
| 2.7 | Pagar total | Estado `paid`, mesa **Libre** | |
| 2.8 | Abrir otra sesión y ver la mesa cambiar sin recargar | Actualización en vivo por WebSocket | |
| 2.9 | Cancelar una orden sin pagos | Mesa libre, estado `cancelled` | |

## 3. Administración

| # | Prueba | Resultado esperado | ✅/❌ |
|---|---|---|---|
| 3.1 | Crear/editar/desactivar categoría y producto | Cambios visibles para el mesero | |
| 3.2 | Crear mesa y usuario mesero | Aparecen en sus listados | |
| 3.3 | Resetear password de un mesero | El mesero entra con la nueva clave, no con la vieja | |
| 3.4 | Intentar desactivarse a sí mismo | 409 / error en la UI | |

## 4. Reportes

| # | Prueba | Resultado esperado | ✅/❌ |
|---|---|---|---|
| 4.1 | Abrir `/report` con fecha de hoy | Total, por mesa y por producto (solo órdenes pagadas) | |
| 4.2 | Exportar CSV | Descarga `corte-YYYY-MM-DD.csv`, abre en Excel con acentos | |
| 4.3 | Consultar `/orders` con otra fecha | Historial coherente con los pagos del día | |

## 5. Operación

| # | Prueba | Resultado esperado | ✅/❌ |
|---|---|---|---|
| 5.1 | Ejecutar `infra/backup.sh` | Se crea `backups/posbar-<fecha>.dump` | |
| 5.2 | Ejecutar `infra/restore.sh <backup>` | Restaura tras confirmar; `/health/ready` en verde | |
| 5.3 | Reiniciar el servidor/VPS | Los contenedores arrancan solos, migraciones y seed idempotentes | |
| 5.4 | Revisar logs del stack | Sin 5xx y sin errores de WebSocket | |

## Firma

| Rol | Nombre | Fecha | Firma |
|---|---|---|---|
| Cliente | | | |
| Desarrollo | | | |

**Observaciones:**
```text

```
