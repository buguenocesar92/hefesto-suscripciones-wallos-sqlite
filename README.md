# Hefesto Suscripciones · Wallos 5.8.3 + SQLite

Seguimiento de gastos recurrentes, proveedores, categorías y próximos pagos. Kit de despliegue nativo para Coolify/VPS con alta privada, bloqueo de registro abierto al arrancar en producción, respaldo completo y restauración.

## Stack y alcance
Wallos usa PHP8.3, Nginx y SQLite. Este paquete no utiliza Supabase: el producto consulta SQLite directamente y no ofrece conexión PostgreSQL intercambiable. Forzarla requeriría modificar y mantener el producto. Se conservan interfaz y funciones nativas.

No cobra suscripciones a clientes, no conecta bancos y no genera documentos tributarios. Registra obligaciones/gastos y ayuda a revisarlos. Para facturación/cobranza utilizar otro sistema y definir integración aparte.

Persisten dos volúmenes: /var/www/html/db y /var/www/html/images/uploads/logos (incluye avatares). Base, preferencias, tokens y claves de notificación deben viajar juntas. Una instancia por cliente recomendada; múltiples usuarios no equivalen a permisos de un ERP.

## Instalación
Requisitos: Docker25+ y Compose v2, Python3.11+ para scripts, dominio y proxy HTTPS. Arranque orientativo: 1CPU/1GB para uso pequeño; medir importaciones y tareas antes de fijar capacidad.

1. `python3 scripts/configure.py`. Editar PUBLIC_URL y conservar permiso0600. VOLUME_PREFIX único por instalación.
2. `docker compose -f compose.yaml -f compose.bootstrap.yaml up -d`. Puerto8104 solo en localhost. Acceder por http://localhost:8104 o túnel `ssh -L 8104:127.0.0.1:8104 usuario@servidor`.
3. Crear primera cuenta desde interfaz. No hay credencial compartida. Revisar contraseña, idioma, zona horaria, moneda y categorías.
4. En administración cerrar nuevos registros y mantener login habilitado. No activar modo sin login. Crear las cuentas necesarias durante esta ventana privada. Revisar MFA disponible en la edición antes de habilitar acceso remoto.
5. Cargar manualmente examples/gastos-demo.csv como referencia (no es importador automático). Comprobar calendario, recurrencia y totales. No introducir tarjetas ni credenciales de proveedores.
6. `docker compose -f compose.yaml -f compose.bootstrap.yaml down` (sin -v). Definir INITIAL_SETUP_COMPLETE=true y PUBLIC_URL=https://suscripciones.sudominio.
7. `docker compose up -d`. La comprobación de arranque exige usuarios existentes, registro cerrado y login activo. En Coolify importar compose.yaml con ops y .env; apuntar dominio HTTPS al servicio app:80. No añadir bootstrap en producción.
8. Probar login, edición, persistencia y endpoints protegidos. /db/wallos.db, /db/wallos.db-wal, /db/setup_token.db deben devolver403. El montaje Nginx refuerza protección del directorio entero, conservando reglas upstream.

El control de arranque no impide que un administrador cambie opciones después: mantener política de registro cerrado. No es una auditoría continua de permisos. Imagen oficial fijada por digest, entrypoint dumb-init y startup nativo preservados; este necesita root para preparar permisos y servicios. PUID/PGID82.

## Avisos y tareas
No se configuran credenciales SMTP ni proveedores de notificaciones. Configurarlos en interfaz únicamente cuando se conozca destinatario/canal y realizar prueba autorizada. Los recordatorios dependen de tareas internas y de la entrega del proveedor; comprobarlos en el servidor. No añadir otro cron externo sin revisar el programador de esta versión: el arranque nativo modifica su crontab.

La app puede consultar servicios externos para tipos de cambio y actualizaciones al iniciar. No se han enviado mensajes desde este kit. En restauraciones de ensayo usar red aislada para evitar reenviar avisos con credenciales recuperadas.

## Respaldos
`python3 scripts/backup.py` detiene la app y sus tareas, copia íntegros db y logos y la configuración, genera manifest/hashes y reinicia si estaba activa. Ejecutar sobre compose base, fuera de bootstrap, sin importaciones en curso.

`python3 scripts/check_backup.py /ruta/respaldo` comprueba hashes e integridad SQLite en una copia temporal sin Docker. Cifrar y guardar respaldo fuera del servidor; contiene información de gastos y posibles secretos. Restaurar siguiendo docs/RESTORE.md.

Estado: validación estática y pruebas de scripts sobre SQLite sintético. No se ejecutó Docker, Wallos, correo ni restauración real. Antes de producción completar docs/ACCEPTANCE.md.

## Despliegue en Coolify (MVP Hefesto)

Coolify importa `compose.yaml` con build pack Docker Compose y pone TLS y
dominio. El servicio `app` queda detrás de Traefik; nada publica puertos
directos ni monta `docker.sock`. El arranque exige `INITIAL_SETUP_COMPLETE=true`,
base con al menos un usuario y registro cerrado (lo verifica `ops/start.sh`).

Antes del primer despliegue en Coolify hay que hacer el alta previa en local
o por túnel SSH, sobre el mismo volumen persistente, porque
`INITIAL_SETUP_COMPLETE=true` aborta si no hay un usuario y el registro no
está cerrado:

1. Levantar `compose.yaml` con `compose.bootstrap.yaml` y `BOOTSTRAP_MODE=true`
   en `127.0.0.1:8104` (solo en localhost, jamás expuesto).
2. Crear la primera cuenta y revisar idioma, zona horaria, moneda y
   categorías.
3. En administración cerrar el registro y dejar login habilitado.
4. Bajar el stack (`docker compose … down`, sin `-v`) y recién ahí
   desplegar `compose.yaml` en Coolify con `INITIAL_SETUP_COMPLETE=true`.

Variables de entorno que Coolify debe poblar antes del primer arranque:

- `PUBLIC_URL`: URL HTTPS definitiva del servicio (por ejemplo,
  `https://suscripciones.sudominio`). Es obligatoria y se inyecta en
  `WALLOS_SERVER_URL`.
- `INITIAL_SETUP_COMPLETE`: en Coolify se pone siempre en `true`. El arranque
  `ops/start.sh` aborta si no vale `true`, así que dejarla en `false` haría
  reiniciar el contenedor en bucle. El alta previa se hace con
  `compose.bootstrap.yaml` y `BOOTSTRAP_MODE=true` como se describe arriba.
- `VOLUME_PREFIX`: variable a definir en Coolify con un valor único por
  instancia (por ejemplo, el slug del cliente). El kit fija el `name:` del
  volumen a partir de este prefijo, de modo que dos despliegues con el mismo
  valor compartirían la misma base. Si se omite, se usa el valor por defecto
  `hefesto-suscripciones`; ese valor es adecuado solo para un único
  despliegue de prueba en la misma máquina.

`compose.yaml` es el único archivo que Coolify importa. `compose.bootstrap.yaml`
y `compose.isolated.yaml` **no se cargan en Coolify**:

- `compose.bootstrap.yaml` publica `127.0.0.1:8104:80`, lo que viola el
  contrato del despliegue (nada debe exponer puertos directos). Solo se usa
  en local o por túnel SSH sobre el mismo volumen para el alta previa.
- `compose.isolated.yaml` es para ensayos de restauración en red aislada
  fuera de Coolify; bloquea la salida a Internet para no reenviar avisos con
  credenciales recuperadas.
