===================
Workshop Management
===================

Gestión de taller mecánico sobre Odoo 19 Community: entrada de vehículos,
órdenes de trabajo y facturación.

Qué hace
========

* **Nuevo ingreso**: registra un coche que entra hoy con matrícula, cliente,
  teléfono, DNI y los trabajos a realizar. Genera el nº de orden (B001, B002…)
  automáticamente.
* **Coches en el taller**: tablero con las órdenes abiertas. Al cerrar una
  orden el coche desaparece del tablero y queda en el historial.
* **Impresión**: ficha de la orden en PDF con QR del nº de orden y hueco para
  la firma del cliente.
* **Facturación**: botón *Crear factura* en la orden. Se pueden añadir
  conceptos extra antes de facturar. La factura es una `account.move` estándar,
  con su PDF legal y su envío por email nativos.
* **Historial**: por matrícula (modelo `workshop.vehicle`, creado solo) y por
  cliente (`res.partner`).

Diseño
======

No se modifica el core. Solo herencia:

* `account.move` → campo `workshop_order_id` (trazabilidad).
* `res.partner` → botón inteligente con las órdenes del cliente.

No se reutiliza `repair` (exige producto de stock propio desde Odoo 17) ni
`fleet` (modela la flota de la empresa, no vehículos de cliente).

Los importes se calculan siempre con `account.tax.compute_all()`; nunca se
calcula el IVA a mano.

Configuración
=============

* El prefijo y el relleno del número de orden se cambian en
  *Ajustes → Técnico → Secuencias → Orden de taller* (código `workshop.order`),
  sin tocar código.
* Grupos de acceso: *Operario* (crea, edita y cierra órdenes) y *Responsable*
  (además anula órdenes y borra fichas).

Créditos
========

* Vykia

Licencia: AGPL-3
