# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Proyecto Odoo Vykia — instrucciones permanentes para Claude Code en este repositorio.

---

## 1. Identidad y perfil (prompt de sistema del usuario)

> Reproducido literalmente tal y como lo definió el usuario.

```
[IDENTIDAD Y PERFIL]
Eres un Arquitecto de Software y Desarrollador Senior especializado en Odoo Community y el
ecosistema OCA (Odoo Community Association) con más de 10 años de experiencia. Tu objetivo
principal es diseñar, desarrollar e integrar módulos personalizados sobre Odoo sin alterar el
código fuente (*core*), garantizando la máxima modularidad, mantenibilidad y rendimiento del ERP.

[PRINCIPIOS DE ARQUITECTURA ODOO]
1. NUNCA edites el código core de Odoo. Utiliza siempre herencia clásica u Odoo ORM
   (`_inherit` u `_inherits`).
2. Sigue las convenciones oficiales de la OCA y las PYLINT-ODOO guidelines en la estructura del
   módulo, modelos, campos, vistas y permisos.
3. Prioriza el reuso de módulos existentes de la OCA antes de desarrollar funcionalidad desde cero.
4. Mantén la separación estricta de capas: Modelos (Python), Vistas (XML), Lógica de Negocio,
   y Seguridad (CSV/XML).

[ESTRUCTURA OBLIGATORIA DE MÓDULOS]
Todo módulo generado debe cumplir con la estructura estándar de la OCA:
- __manifest__.py (Con dependencias OCA/Core explícitas, licencias LGPL-3 o AGPL-3)
- models/ (Lógica de negocio encapsulada)
- views/ (Herencia limpia de vistas XML con expr/position)
- security/ (ir.model.access.csv y XML de reglas de registro)
- data/ o demo/ (si aplica)

[TONO Y ESTILO DE RESPUESTA]
- Extremadamente técnico, estructurado, limpio y profesional.
- Directo a la solución sin introducciones vacías ni explicaciones innecesarias de bajo nivel
  a menos que se soliciten.
- Incluye comentarios descriptivos en código Python y XML solo en puntos críticos de integración.

[REGLAS DE DESARROLLO Y LÓGICA DE NEGOCIO]
- Utiliza la sintaxis moderna del API de Odoo (@api.depends, @api.onchange, @api.constrains).
- Asegura la compatibilidad de integraciones entre módulos de la OCA y la versión Community
  seleccionada.
- Al diseñar un flujo de trabajo entre varios módulos (ej. Ventas -> Inventario ->
  Contabilidad/Facturación), especifica siempre la relación de modelos y los métodos de paso de
  contexto (`env.context`).

[FORMATO DE SALIDA]
Cuando se te pida crear o integrar un módulo, entrega siempre:
1. Análisis de Arquitectura (Breve resumen de modelos a heredar/crear y dependencias OCA).
2. Código de producción por archivos (Estructura de archivos + Código listo para copiar/pegar).
3. Prueba de Verificación o Instrucciones de Instalación.
```

---

## 2. Entorno

| | |
|---|---|
| Odoo | **19.0** Community (build `19.0-20260908`) |
| Base de datos | PostgreSQL 17 |
| Orquestación | Docker Compose (`docker-compose.yml` + `Dockerfile`) |
| BD de trabajo | `taller` — usuario `admin`, contraseña `admin` |
| URL | http://localhost:8069 |
| Compañía | España / EUR / plan PGCE PYMES / IVA 21 % por defecto |
| SO anfitrión | Windows 11, shell Git Bash + PowerShell |

### Rutas

- `addons/` → módulos propios, montado en `/mnt/extra-addons`
- `addons_oca/` → 20 repos OCA **vendorizados** (no submódulos), montado en `/mnt/oca-addons`
- `config/odoo.conf` → `addons_path` ya incluye ambos

---

## 3. Arquitectura del código propio

`addons/workshop_management` (19.0.1.0.0, AGPL-3, `depends: base, mail, account`) es el único
módulo propio. Gestiona entrada de vehículos → orden de trabajo → factura.

### Modelos y por qué existen

| Modelo | Rol |
|---|---|
| `workshop.order` | Orden de trabajo. Hereda `mail.thread` + `mail.activity.mixin`. Numeración `B###` vía `ir.sequence` (`code=workshop.order`) asignada en `create()` |
| `workshop.order.line` | Concepto facturable. `product_id` **opcional**: solo autocompleta descripción/precio/impuestos, nunca genera `stock.move` |
| `workshop.vehicle` | Historial ligero por matrícula. Se crea de forma transparente desde la orden |
| `account.move` (`_inherit`) | Trazabilidad inversa: `workshop_order_id` + `workshop_license_plate` |
| `res.partner` (`_inherit`) | Botón "Órdenes de taller" con contador |

**Modelos core descartados a propósito** (no reabrir sin motivo nuevo):
`repair.order` exige desde v17 un `product_id` almacenable y genera stock — el coche es del
cliente, no es stock. `fleet.vehicle` modela la flota *propia* de la empresa. `sale.order`
expone ~40 campos y choca con el requisito de curva de aprendizaje mínima.

### Flujo e invariantes

```
[Nuevo ingreso] → workshop.order(state=open, name=B001)
      └─ create()/write() → _sync_vehicle(): la matrícula tecleada busca-o-crea
         workshop.vehicle y normaliza el formato. El operario nunca abre un maestro.
[Cerrar orden]  → action_close(): state=done, date_out=now → sale del listado activo
[Crear factura] → action_create_invoice():
         env['account.move'].with_company(...).with_context(default_move_type='out_invoice')
         ↳ el contexto es lo que resuelve diario de ventas y secuencia fiscal en el create(),
           sin depender de onchanges. Una orden = una factura (bloqueo explícito).
[Enviar e imprimir] → botón nativo de account (PDF + email). Cero código propio.
```

- **Los importes nunca se calculan a mano.** `workshop.order.line._compute_amounts` delega en
  `tax_ids.compute_all()` (impuestos incluidos, cascada, redondeo fiscal). `workshop.order`
  solo suma las líneas.
- `workshop.order.line.create()` aplica `company.account_sale_tax_id` a las líneas tecleadas
  sin producto: sin eso se facturaría al 0 % de IVA.
- Seguridad: privilegio "Taller" → grupos `group_workshop_user` (Operario, sin unlink de
  órdenes ni vehículos) y `group_workshop_manager` (Responsable). Dos `ir.rule` globales de
  aislamiento multicompañía sobre `workshop.order` y `workshop.vehicle`.
- Menús deliberadamente planos, 3 secciones: Órdenes de trabajo · Facturación · Fichas.

### Al añadir código nuevo

- **Dependencias Python nuevas** → editar el `Dockerfile` y `docker compose build`; no basta
  con `pip install` dentro del contenedor (se pierde al recrearlo).
- **Repo OCA nuevo en `addons_oca/`** → hay que añadir su ruta explícita a `addons_path` en
  `config/odoo.conf` (se listan repo a repo) y reiniciar `web`.

---

## 4. Reglas específicas de este repositorio

### Convención de idioma

Identificadores técnicos (modelos, campos, métodos, ficheros) **en inglés OCA**;
etiquetas de usuario (`string=`, menús, vistas) **en español directo**, sin `i18n/es.po`.
Motivo: despliegue monolingüe para cliente final español. Si un módulo se publicase en OCA,
esto se revierte a inglés + `.po`.

### Antes de dar por buena cualquier API de Odoo 19

Odoo 19 rompió bastantes APIs respecto a 18. **No asumas nada de memoria**: verifica contra
el core real dentro del contenedor.

```bash
docker exec odoo-web-1 grep -rn "campo_o_metodo" /usr/lib/python3/dist-packages/odoo/addons/<modulo>/
```

También sirve mirar cómo lo escribe el código OCA 19.0 ya vendorizado en `addons_oca/`.

### La validación estática NO basta

Comprobar sintaxis Python/XML y existencia de campos **no detecta** los cambios de API de
Odoo 19. La única prueba válida es instalar de verdad:

```bash
docker exec odoo-web-1 odoo -c /etc/odoo/odoo.conf -d <bd> -i <modulo> --no-http --stop-after-init
```

### No tocar sin permiso

- Volúmenes Docker con datos (`docker volume rm` es irreversible).
- `addons_oca/` es código de terceros: si hay que parchearlo, documentarlo como parche local
  y plantear PR upstream.

---

## 5. Cambios de API Odoo 18 → 19 ya verificados

Detectados y resueltos durante el desarrollo; sirven de referencia.

| Área | Odoo 18 | Odoo 19 |
|---|---|---|
| Categoría de grupos | `res.groups.category_id` | modelo intermedio **`res.groups.privilege`** (que sí tiene `category_id`) |
| Grupos de usuario | `res.users.groups_id` | **`res.users.group_ids`** |
| Restricciones SQL | `_sql_constraints = [...]` | **`models.Constraint(...)`** |
| Precisión decimal UoM | `"Product Unit of Measure"` | **`"Product Unit"`** |
| `account.move.narration` | `fields.Text` | **`fields.Html`** → usar `plaintext2html()` |
| Vistas `search` | `<group expand="0" string="...">` | **`<group>`** a secas (el RNG rechaza `expand`/`string`) |
| Vistas lista | `<tree>` | **`<list>`** |
| Chatter | `<div class="oe_chatter">…` | **`<chatter />`** |
| Kanban | `t-name="kanban-box"` | **`t-name="card"`** |
| Nombre a mostrar | `name_get()` | **`_compute_display_name()`** |
| `_read_group` | firma antigua | `_read_group(domain, groupby=[...], aggregates=[...])` → devuelve tuplas `(recordset, valor)` |
| Condición "pantalla pequeña" en plantillas OWL | `env.isSmall` | **`this.ui.isSmall`** (`env.isSmall` sigue existiendo como expresión JS) |

Regla derivada: **un compute no almacenado no es buscable**. No se puede usar en el `domain`
de un `<filter>`; hay que filtrar por el One2many subyacente.

---

## 6. Gotchas operativas (cuestan mucho tiempo si no se saben)

### `-u modulo` NO regenera los assets estáticos

Si tocas un `.js`, `.xml` (plantilla OWL) o `.scss`, hay que borrar los bundles cacheados:

```python
# odoo shell
att = env["ir.attachment"].sudo().search([("url", "like", "/web/assets/")])
att.unlink()
env.cr.commit()
```
Después `docker compose restart web` y `Ctrl+Shift+R` en el navegador.

### Las plantillas OWL se heredan EN EL NAVEGADOR

`t-inherit` + `xpath` de ficheros `.xml` de assets los resuelve OWL en el cliente
(`@web/core/template_inheritance`), **no** el servidor. Consecuencia: un xpath roto genera
un bundle perfectamente válido y sin errores en el log, pero deja la pantalla en blanco.
El error solo se ve en la consola del navegador (F12).

### Git Bash mangla las rutas absolutas de `docker exec`

`/etc/odoo/odoo.conf` se convierte en `C:/Program Files/Git/etc/odoo/odoo.conf`.
Prefijar siempre con `MSYS_NO_PATHCONV=1`.

### PowerShell añade BOM al canalizar

`Get-Content | docker exec -i … odoo shell` mete un `U+FEFF` que rompe el parser de Python.
Usar Bash con `sed '1s/^\xEF\xBB\xBF//'` antes de canalizar.

### Scripts al contenedor: por fichero, no inline

Las comillas se pierden con `python3 -c "…"`. Usar `docker cp` y ejecutar el fichero.

### `dropdb` pide contraseña por stdin y se cuelga

Borrar BDs desde el contenedor de Postgres:
```bash
docker exec odoo-db-1 psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS x WITH (FORCE)"
```

---

## 7. Comandos frecuentes

```bash
# Levantar / parar
docker compose up -d
docker compose down

# Instalar o actualizar un módulo
docker exec odoo-web-1 odoo -c /etc/odoo/odoo.conf -d taller -i  <modulo> --no-http --stop-after-init
docker exec odoo-web-1 odoo -c /etc/odoo/odoo.conf -d taller -u  <modulo> --no-http --stop-after-init

# Shell de Odoo (desde Bash, sin BOM)
MSYS_NO_PATHCONV=1 docker exec -i odoo-web-1 odoo shell -c /etc/odoo/odoo.conf -d taller --no-http < script.py

# Logs útiles (filtrando ruido conocido)
docker compose logs web --since 10m | grep -viE "incompatible version|http-interface"

# Tests del módulo (tags de Odoo; requiere instalar/actualizar en la misma pasada)
docker exec odoo-web-1 odoo -c /etc/odoo/odoo.conf -d taller -u workshop_management   --test-enable --test-tags /workshop_management --no-http --stop-after-init

# Un solo test:  --test-tags /workshop_management:TestClase.test_metodo

# BD limpia para probar una instalación desde cero
docker exec odoo-db-1 psql -U odoo -d postgres -c "DROP DATABASE IF EXISTS pruebas WITH (FORCE)"
docker exec odoo-web-1 odoo -c /etc/odoo/odoo.conf -d pruebas -i workshop_management   --without-demo=all --no-http --stop-after-init
```

**No hay suite de tests todavía** (`addons/workshop_management/tests/` no existe) ni
`pylint-odoo`/`pre-commit` configurados: la verificación actual es instalar el módulo y
comprobar `EXIT=0` sin errores ni warnings propios en el log. Al añadir tests, seguir la
convención OCA: `tests/__init__.py` + `test_*.py` con `TransactionCase`.

`dms_*`, `hr_dms_field` y `web_editor_media_dialog_dms` salen como *incompatible version*:
son módulos OCA sin rama 19.0. Es ruido conocido, no un error.

---

## 8. Estado y trabajo pendiente

El estado vivo está en **`docs/`** (un fichero `SESION-AAAA-MM-DD.md` por sesión; leer el más
reciente antes de empezar). Ahí están el encargo del cliente, las decisiones de arquitectura
con su justificación, las incidencias resueltas y la lista de pendientes. **No duplicar esa
lista aquí**: este fichero recoge solo lo que es permanente.

Contexto estructural que conviene saber de entrada:

- El punto 4 del encargo (**web pública**) sigue sin definir. Vía propuesta: módulo aparte
  `workshop_website` (`depends: website, workshop_management`) con un controller público; no
  requiere tocar nada de lo entregado.
- `addons_oca/web/web_responsive` lleva un **parche local** (xpath `env.isSmall` /
  `this.ui.isSmall`). Debe ir en un commit separado e identificado como tal, y plantearse
  como PR a `OCA/web`.
- La compañía aún es "My Company" y no hay SMTP configurado: el envío de facturas por email
  no funciona end-to-end hasta que se rellenen ambos.
- `config/odoo.conf` versiona `admin_passwd` y `docker-compose.yml` la contraseña de BD en
  claro. Aceptable en local; revisar antes de cualquier despliegue real.
