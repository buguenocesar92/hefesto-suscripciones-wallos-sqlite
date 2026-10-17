#!/bin/sh
set -eu
if [ "${BOOTSTRAP_MODE:-false}" != true ]; then
  [ "${INITIAL_SETUP_COMPLETE:-false}" = true ] || { echo 'Complete instalación privada antes de publicar'; exit 1; }
  case "${WALLOS_SERVER_URL:-}" in https://*) ;; *) echo 'Configurar URL HTTPS'; exit 1;; esac
  db=/var/www/html/db/wallos.db
  [ -s "$db" ] || { echo 'Falta base inicializada'; exit 1; }
  count=$(sqlite3 -readonly "$db" 'SELECT count(*) FROM user;')
  [ "$count" -gt 0 ] || { echo 'Falta usuario'; exit 1; }
  safe=$(sqlite3 -readonly "$db" 'SELECT count(*) FROM admin WHERE id=1 AND registrations_open=0 AND login_disabled=0;')
  [ "$safe" = 1 ] || { echo 'Cerrar registro y mantener login habilitado en administración'; exit 1; }
fi
exec /var/www/html/startup.sh
