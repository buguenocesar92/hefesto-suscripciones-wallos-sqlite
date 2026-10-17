# Antes de ofrecer producción
- docker compose config --quiet y arranque Docker25+.
- Registrar propietario por túnel, cerrar registro y verificar que modo producción rechaza base sin usuarios/registro abierto/login deshabilitado.
- Login HTTPS, cierre de sesión y aislamiento entre dos usuarios.
- Registrar gasto de prueba en CLP y USD; revisar monto, ciclo, fechas, cancelación y calendario.
- Verificar scheduler nativo actualiza vencimientos; probar aviso solo con canal autorizado.
- Reiniciar y comprobar DB/logos; revisar permisos82 y logs.
- Acceso HTTP a /db/ y archivos SQLite/WAL/token denegado.
- Backup, integrity_check y restauración en volúmenes nuevos con salida de red bloqueada durante ensayo.
- Definir límites de carga/importación en proxy; upstream admite hasta256MB.
- Vigilar disco, salud y fallos de tareas. Ensayar actualización en copia aislada antes del corte.

Local: se verificaron Python, YAML, shell y ZIP, y control de integridad con SQLite de prueba. No equivale a probar aplicación real.
