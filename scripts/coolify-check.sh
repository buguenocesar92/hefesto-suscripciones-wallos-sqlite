#!/usr/bin/env bash
# Comprueba que el compose que Coolify importa cumple el contrato del plan:
#   - Punto 1: nada que salte Traefik ni dé poder sobre el host.
#   - Punto 2: nombres estables sin forzar (sin `name:` a nivel raíz, en redes
#     ni en volúmenes con un literal; los volúmenes con ${VAR:-default} sí
#     están permitidos).
#
# Renderiza el compose con un .env sintético (no contiene secretos reales) y
# recorre el JSON resultante con jq para detectar las violaciones del
# apartado "servicios". La parte de nombres (root, redes, volúmenes
# literales) la inspeccionamos sobre el YAML original, porque en el JSON
# renderizado docker compose ya resolvió ${VAR:-default} y todo parece
# literal. Termina con código 0 si el compose pasa y != 0 en caso contrario.
#
# Uso: bash scripts/coolify-check.sh
set -euo pipefail

# Dependencias: jq, docker compose y el módulo yaml de Python3. Sin ellas el
# chequeo no puede ejecutarse; avisamos y abortamos con código distinto de 0
# en lugar de fallar más adelante con mensajes crípticos.
command -v jq >/dev/null 2>&1 || { echo "FAIL: falta jq en PATH"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "FAIL: falta docker en PATH"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "FAIL: falta el plugin docker compose"; exit 1; }
python3 -c 'import yaml' 2>/dev/null || { echo "FAIL: falta el módulo yaml de python3"; exit 1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Único compose que Coolify importa. Los compose.bootstrap.yaml y
# compose.isolated.yaml son de uso local (instalación privada y ensayo) y el
# propio contrato del plan los exime de las reglas estrictas.
COMPOSE="$REPO_ROOT/compose.yaml"

# .env sintético y efímero. mktemp usa $TMPDIR y se borra al salir.
TMP_ENV="$(mktemp)"
cleanup() { rm -f "$TMP_ENV"; }
trap cleanup EXIT

# Devuelve, una por línea, el nombre de cada ${VAR} referenciado en $1 (con
# cualquier modificador :-default, :?error, ::-default ya recortado).
collect_vars() {
  awk '{
    line = $0
    while (match(line, /\$\{[A-Za-z_][A-Za-z0-9_]*(:[^}]*)?\}/)) {
      v = substr(line, RSTART, RLENGTH)
      sub(/^\$\{/, "", v)
      sub(/\}$/, "", v)
      sub(/:.*$/, "", v)
      print v
      line = substr(line, RSTART + RLENGTH)
    }
  }' "$1" | sort -u
}

# Valor ficticio para una variable. URL/host → https://ejemplo.invalid;
# el resto → cadena opaca no usada por la app en este repo.
fake_value() {
  case "$1" in
    PUBLIC_URL|WALLOS_SERVER_URL) printf 'https://ejemplo.invalid\n' ;;
    *) printf 'x123example\n' ;;
  esac
}

# Inspecciona el YAML original y reporta:
#   - name: a nivel raíz
#   - name: dentro de cada red
#   - name: literal dentro de cada volumen (los que contienen ${VAR...} están
#     permitidos; el resto viola el contrato)
# Devuelve un mensaje por línea, vacío si todo está bien.
check_yaml_names() {
  python3 - "$1" <<'PY'
import sys, re, yaml
path = sys.argv[1]
with open(path) as f:
    data = yaml.safe_load(f) or {}
problems = []
if isinstance(data, dict) and 'name' in data:
    problems.append(f"root: tiene name: fijo a nivel raíz ({data['name']!r})")
for net_key, net_val in (data.get('networks') or {}).items():
    if isinstance(net_val, dict) and 'name' in net_val:
        problems.append(f"networks.{net_key}: tiene name: fijo ({net_val['name']!r})")
# Volumen con `name:` permitido solo si es una referencia ${VAR:-default}
# parametrizable; los nombres literales rompen la regla 2 del contrato
# (Coolify asigna el nombre del proyecto y dos instancias compartirían
# volumen si el default coincide).
DEFAULT_RE = re.compile(r'\$\{[A-Za-z_][A-Za-z0-9_]*:?-[^}]+\}')
for vol_key, vol_val in (data.get('volumes') or {}).items():
    if not isinstance(vol_val, dict):
        continue
    name = vol_val.get('name')
    if name is None:
        continue
    sname = str(name)
    if '${' not in sname:
        problems.append(f"volumes.{vol_key}: tiene name: literal ({sname!r})")
    elif not DEFAULT_RE.search(sname):
        problems.append(f"volumes.{vol_key}: name sin valor por defecto ({sname!r})")
print('\n'.join(problems))
PY
}

# Detecta violaciones en el JSON renderizado (reglas por servicio).
check_rendered_services() {
  local cfg="$1"
  jq -r --arg repo "$REPO_ROOT" '
    (.services // {}) | to_entries[] |
    select(((.value.profiles // []) | length) == 0) |
    .key as $svc |
    (.value // {}) |
    (
      (if (.ports // null) != null then [$svc, "tiene ports"] else empty end),
      (if (.container_name // null) != null then [$svc, "container_name fijo"] else empty end),
      (if (.privileged // false) == true then [$svc, "privileged=true"] else empty end),
      (if (.cap_add // null) != null then [$svc, "cap_add definido"] else empty end),
      (if (.devices // null) != null then [$svc, "devices definido"] else empty end),
      (if (.network_mode // null) == "host" then [$svc, "network_mode host"] else empty end),
      (if (.pid // null) == "host" then [$svc, "pid host"] else empty end),
      (if (.ipc // null) == "host" then [$svc, "ipc host"] else empty end),
      (if ((.security_opt // []) | map(select(test("unconfined"))) | length) > 0 then [$svc, "security_opt unconfined"] else empty end),
      (if ((.volumes // []) | map(select(type == "object" and ((.source // "") | startswith("/")) and ((.source // "") != $repo) and ((.source // "") | startswith($repo + "/") | not))) | length) > 0 then [$svc, "bind fuera del repo"] else empty end),
      (if ((.volumes // []) | map(select(type == "object" and ((.source // "") | test("docker\\.sock")))) | length) > 0 then [$svc, "monta docker.sock"] else empty end)
    ) | join(": ")
  ' <<<"$cfg"
}

# --- Render ---------------------------------------------------------------

echo "=== $COMPOSE ==="

: > "$TMP_ENV"
while IFS= read -r v; do
  [[ -n "$v" ]] || continue
  printf '%s=%s\n' "$v" "$(fake_value "$v")" >> "$TMP_ENV"
done < <(collect_vars "$COMPOSE")

# Render con docker compose. stderr se descarta: las "WARNING" sobre el
# config.json de docker no aportan al contrato del plan.
cfg="$(docker compose --project-directory "$(dirname "$COMPOSE")" -f "$COMPOSE" --env-file "$TMP_ENV" config --format json 2>/dev/null)" || {
  echo "FAIL: docker compose no renderiza $COMPOSE"
  exit 1
}

bad=""
yaml_bad="$(check_yaml_names "$COMPOSE")"
[[ -n "$yaml_bad" ]] && bad+="$yaml_bad"$'\n'

svc_bad="$(check_rendered_services "$cfg")"
[[ -n "$svc_bad" ]] && bad+="$svc_bad"$'\n'

if [[ -n "$bad" ]]; then
  echo "FAIL: $COMPOSE viola el contrato de Coolify"
  printf '%s\n' "$bad" | sed 's/^/  /'
  exit 1
fi

echo "OK: $COMPOSE cumple el contrato"