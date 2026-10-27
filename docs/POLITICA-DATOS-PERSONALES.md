# Política de tratamiento de datos personales — Suscripciones (Hefesto Studio)

Estado: vigente desde 2026-10-20. Responsable del tratamiento: el cliente que
opera el kit. Este documento describe qué datos guarda el kit, por qué, cuánto
tiempo los retiene y cómo se exercise los derechos del titular (Ley 21.719).

## 1. Qué datos guarda este kit

El kit de suscripciones (Wallos) guarda, por persona suscrita:

- **Suscripcion**: nombre y correo del suscriptor, plan contratado, importe,
  fecha de alta, periodicidad y estado (activa, cancelada, pausada).
- **Estado de pago**: ultimo pago registrado, importe y metodo; no guarda datos
  de tarjeta ni de cuenta bancaria.
- **Servicios y recordatorios**: notificaciones de cobro y de renovacion.
- **Cuentas del panel**: correo, hash de contrasena y rol.
- **Logos personalizados**: archivos de imagen que el cliente sube.
- **Copias locales de respaldo**: `backups/<timestamp>/` con la base SQLite
  (`db.tar.gz`), los logos (`logos.tar.gz`) y la configuracion del kit.

Los datos de suscripcion identifican a personas y sus condiciones
economicas.

## 2. Qué datos NO guarda este kit

- El `.env` **no** se copia en claro al respaldo: solo sus nombres de
  variable (`env.vars`) y, si hay un receptor `age` configurado, el `.env`
  cifrado (`env.age`). Ver `docs/CONTRATO-RESPALDO.md`, regla 5.
- El kit **no** guarda datos de tarjetas, cuentas bancarias ni ningun
  instrumento de pago: Wallos solo registra que un pago ocurrio y cuanto fue.
- El kit no envia los datos de suscripcion a servicios de terceros.

## 3. Base legal y deberes

- **Minimización**: el kit guarda lo necesario para cobrar y avisar: identidad de contacto,
  plan, importe y estado. No pide datos de tarjeta ni de cuenta, ni
  documentos de identidad.
- **Finalidad**: gestionar las suscripciones y sus cobros. Los datos no se usan para otros fines ni se ceden a terceros.
- **Seguridad**: los respaldos se cifran en reposo con `age` hacia el destino del operador, la clave privada no está en este servidor y el `.env` nunca sale en claro.
- **Auditoría**: cada respaldo y cada restauración dejan registro en `logs/restore.log` con origen, sha256 verificado, destino y resultado. Es registro de actividades de tratamiento: no guarda valores de secretos ni importes.

## 4. Retención

| Dato | Dónde | Retención por defecto | Quién lo borra |
|---|---|---|---|
| Suscriptores y suscripciones | volumen `db` (SQLite) | mientras el cliente los mantenga | el operador, desde la interfaz |
| Historial de pagos | volumen `db` | mientras el cliente lo mantenga | el operador |
| Cuentas del panel | volumen `db` | mientras la cuenta exista | el operador |
| Logos | volumen `logos` | mientras el cliente los mantenga | el operador |
| Respaldos en disco | `backups/<timestamp>/` | **a definir por el operador**; el kit no borra nada por su cuenta | el operador |
| Registro de auditoría | `logs/restore.log` | append-only; se trunca por política del cliente | el operador |

**El kit no borra respaldos ni datos por su cuenta.** Borrar es una decisión del
operador, porque un respaldo borrado no se recupera.

## 5. Derechos del titular (acceso, rectificación y supresión)

El cliente que opera el kit debe poder atender las solicitudes de sus
titulares:

1. **Acceso**: entregar los datos de una suscripcion concreta (plan, importe,
   estado) al titular que lo solicite.
2. **Rectificación**: corregir nombre, correo o estado desde la interfaz.
3. **Supresión**: eliminar la suscripcion y, cuando corresponda, la cuenta y
   los respaldos que la contengan; dejar constancia en el registro de auditoria.
4. **Revocación del consentimiento**: si el tratamiento depende del
   consentimiento, eliminar la suscripcion y detener los recordatorios.

El kit garantiza que los datos son localizables, corregibles y borrables; el
cliente es quien conoce la identidad de los titulares.

## 6. Verificación

- `bats tests/backup_restore.bats` comprueba, con datos sintéticos, que el
  `.env` no queda en claro, que el manifiesto lleva las cinco claves, que la
  base SQLite del tar es integra, que un artefacto alterado se rechaza y que
  un destino no vacío aborta la restauración.
- `gitleaks` corre en CI sobre el repositorio y su historial.
