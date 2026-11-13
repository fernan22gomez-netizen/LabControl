# LabControl

## Integrantes

- Fernando Vladimir Obispo Gomez - SMSS024225


## Descripción

LabControl es un prototipo para organizar el inventario de un laboratorio de computación, registrar fallas y guardar el historial de mantenimiento de cada equipo. Presenta alertas para los equipos sin mantenimiento reciente y un resumen de los que acumulan más incidencias.

## Alcance del prototipo

- Registrar equipos con código, estado, ubicación y especificaciones.
- Registrar incidencias por equipo y marcarlas como resueltas.
- Registrar mantenimientos preventivos o correctivos.
- Alertar si un equipo no tiene mantenimiento registrado o han pasado más de 180 días desde el último.
- Mostrar los cinco equipos con más incidencias registradas.
- Permitir el acceso desde computadoras conectadas a la misma red local, sin cuentas de usuario.

El prototipo se limita a un laboratorio. No incluye compras, control de acceso de usuarios ni monitoreo remoto.

## Tecnologías

- **Python:** lenguaje de programación del prototipo.
- **Flask:** presenta la aplicación en el navegador y permite que otras computadoras de la red local accedan al servidor.
- **SQLite (`sqlite3`):** guarda equipos, incidencias y mantenimientos en un archivo local, sin instalar un servidor de base de datos aparte.
- **HTML y CSS:** organizan y presentan los formularios, alertas y reportes.

## Requisitos

- Python 3.10 o superior.
- Una computadora anfitriona y otras computadoras conectadas a la misma red local.
- Instalar la dependencia indicada en `requirements.txt`.

## Ejecución

1. Abre una terminal dentro de la carpeta `LabControl`.
2. (Recomendado) Crea y activa un entorno virtual:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instala Flask:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Inicia la aplicación:

   ```powershell
   py app.py
   ```

5. En la computadora anfitriona, abre `http://127.0.0.1:5000`.
6. Desde otra computadora de la misma red, abre `http://IP-DE-LA-COMPUTADORA-ANFITRIONA:5000`. La computadora anfitriona debe mantener la aplicación en ejecución.

La primera ejecución crea automáticamente `labcontrol.db`. Los datos se conservan en ese archivo local.

## Aplicación en línea

**Enlace para probar LabControl:** [Abrir la aplicación](https://fershy77.pythonanywhere.com)

LabControl permite registrar los equipos del laboratorio, reportar fallas y llevar el historial de mantenimiento. También muestra alertas para equipos que necesitan mantenimiento y un resumen de los que acumulan más incidencias.

Se usó Python con Flask para crear la aplicación web y permitir que se abra desde un navegador. Se eligió SQLite para guardar los registros sin instalar un servidor de base de datos adicional. La app se publicó en PythonAnywhere para que el docente pueda probarla aunque la computadora del grupo esté apagada.

La aplicación no tiene inicio de sesión. Para la demostración, utiliza únicamente datos ficticios.

## Criterio de alerta

Para este prototipo se considera atrasado un equipo que nunca ha recibido un mantenimiento registrado o cuyo último mantenimiento fue hace más de 180 días. El valor se define en `DIAS_ALERTA_MANTENIMIENTO` en `app.py`.

## Nota para la demostración

Pueden registrar dos o tres equipos de ejemplo, agregar incidencias y mantenimientos, y mostrar cómo cambian el contador de incidencias pendientes, la alerta de mantenimiento y el reporte de equipos con más fallas.
