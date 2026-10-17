# Restauración y traspaso
1. Preparar destino nuevo con misma imagen5.8.3 y VOLUME_PREFIX diferente. Mantener origen intacto; no iniciar app todavía.
2. Validar `python3 scripts/check_backup.py /ruta/respaldo`. Recuperar .env y ops desde respaldo confiable y revisar hashes; actualizar dominio/volúmenes. Mantener versión original.
3. `python3 scripts/restore.py /ruta/respaldo`. Exige ambos volúmenes vacíos y app detenida. Valida hashes/rutas antes de extraer; no sobrescribe datos y asigna UID82.
4. Primer ensayo: `docker compose -f compose.yaml -f compose.bootstrap.yaml -f compose.isolated.yaml up -d`. Red Docker interna bloquea salida a Internet; no adjuntar proxy público ni otros servicios. Las consultas externas al iniciar pueden fallar o demorarse: revisar logs. Túnel local para inspección. No configurar proveedores internos accesibles desde esa red durante ensayo.
5. Revisar cuentas, gastos, monedas, fechas, logos y configuración de notificaciones. No asumir envío deshabilitado solo porque .env no contiene claves: Wallos guarda configuración en DB.
6. Detener ensayo sin -v. Para corte final, pausar uso, crear backup final, repetir en volúmenes nuevos y arrancar modo producción. Cambiar DNS y verificar acceso/recordatorios con destinatario autorizado; retirar origen después de aceptar el destino.

Un fallo parcial exige destino limpio. Nunca ejecutar dos instancias escribiendo la misma SQLite ni alojar la base activa en un montaje rclone/NFS. Respaldos a almacenamiento remoto sí, base operativa en disco persistente local.

Odoo: mapear proveedor, nombre, monto, moneda, periodicidad, siguiente vencimiento y categoría hacia modelo acordado. Conservar un identificador de origen para no duplicar registros. Este kit no incluye módulo ni sincronización automática. Revisar exportación disponible en la interfaz y validar columnas antes de importar. No reemplazar la contabilidad con el seguimiento de Wallos.
