# Guía del participante del Laboratorio 2

**Seguridad en DataOps con Python · Comercial Nova · Versión 2.1**

En esta práctica añadirás evidencias y auditoría técnica a un pipeline de pedidos. La base del Laboratorio 1 viene resuelta. Tu trabajo consiste en completar **TODO 5, TODO 6 y TODO 7 en lab2.py**, comprobarlos por separado y explicar los resultados del reporte.

## 1 Qué necesitas y qué entregarás

Necesitas Python 3.12 con venv y pip, un editor, una terminal y conexión para instalar dependencias. No se requieren servicios de nube ni bases de datos. El laboratorio ocupa 60 minutos y la simulación de fallos posterior, 25 minutos. Si no asististe a la sesión anterior, realiza la preparación y el repaso antes del bloque de desarrollo.

Entregarás `lab2.py` con las tres funciones implementadas, las evidencias seleccionadas de ejecución y `evidencias_lab2.md` con tus observaciones. No entregues la clave ni el entorno virtual.

## 2 Qué ocurrió en la sesión anterior

En Comercial Nova protegimos nombre y correo mediante Fernet, detectamos modificaciones con SHA-256 y limitamos operaciones según el rol. El pipeline genera un detalle protegido de 12 pedidos y un resumen de ventas confirmadas por ciudad.

En este paquete, `lab1.py` ya contiene **calcular_hash, autorizar, cifrar y descifrar implementadas**. No hay que resolver TODO 1 a 4 otra vez. Lee [REPASO_LAB1.md](REPASO_LAB1.md): explica el caso, los controles y cómo ejecutar esa práctica con la base resuelta.

En la nueva sesión responderás: ¿qué entrada se procesó?, ¿qué operación se permitió o denegó?, ¿qué control se comprobó? y ¿dónde está la evidencia?

## 3 Preparación desde cero para todos los participantes

Este paquete es autónomo. Aunque hayas asistido a la sesión anterior, puedes comenzar aquí con la base resuelta. No necesitas instalar una versión anterior, trasladar archivos ni seguir una guía de actualización.

Sigue este orden: preparar el entorno, verificar la base, repasar el Laboratorio 1 y completar TODO 5–7. La numeración continúa la sesión anterior; no indica que tengas tareas pendientes de TODO 1–4.

Descomprime el paquete en una carpeta nueva. Abre una terminal dentro de `comercial_nova`, junto a `preparar.py`, `lab1.py` y `lab2.py`. Los archivos Markdown son instrucciones; Python ejecuta los `.py`.

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python preparar.py
$env:DATAOPS_KEY = (Get-Content .secrets/fernet.key -Raw).Trim()
```

Si PowerShell bloquea la activación, no cambies la política del equipo. Después de crear el entorno, usa `.\.venv\Scripts\python.exe` en lugar de `python` para instalar y ejecutar. El comando `$env:DATAOPS_KEY` permanece igual.

En WSL o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python preparar.py
export DATAOPS_KEY="$(cat .secrets/fernet.key)"
```

Elige una sola alternativa. No mezcles entornos de Windows y WSL.

`preparar.py` genera todos los datos ficticios, la referencia y una clave propia. Se ejecuta **una sola vez** y rechaza un entorno que ya tenga esos archivos. No imprime la clave. No se incluyen claves precreadas en el ZIP.

### Cuando retomes la práctica otro día

La preparación inicial termina cuando se generan los datos, la referencia y la clave. En las siguientes sesiones de trabajo conserva esa misma carpeta: activa el entorno y vuelve a cargar `DATAOPS_KEY` con el comando de tu sistema. **No repitas `python preparar.py`.** Continúa desde el TODO en el que te quedaste.

Si encuentras `FileExistsError: Entorno existente; revisar antes de recrear`, comprueba si ya preparaste esa carpeta. Si los tres archivos generados están presentes, carga su clave y ejecuta la verificación de la sección 4. Si la preparación quedó incompleta, conserva la carpeta y descomprime una copia nueva para comenzar, sin mezclar sus archivos.

### Qué debes conservar

| Ruta | Uso |
| --- | --- |
| datos/pedidos.csv | Original conocido de 12 pedidos |
| referencia.sha256 | Huella inicial del original |
| .secrets/fernet.key | Clave local que permite recuperar las salidas |
| datos/pedidos_prueba_parte1.csv | Copia alterada para las pruebas negativas |

No publiques ni imprimas claves. No recalcules la referencia para aceptar una alteración. Al abrir otra terminal, activa el entorno y vuelve a cargar DATAOPS_KEY. La clave nueva de una práctica distinta no descifra salidas antiguas.

## 4 Verifica la base resuelta

Con el entorno activo, guarda los archivos y ejecuta:

```text
python comprobar_1a.py --todo 1
python comprobar_preparacion_lab2.py
```

El primer comando valida el hash y crea la copia alterada si falta. No necesita la clave. Si la copia ya existe y es idéntica, la reutiliza; si tiene otro contenido, se detiene sin sobrescribirla.

El segundo comprueba el original, la referencia, la clave cargada y las funciones y permisos de TODO 1 a 4. Debe terminar con **Preparacion verificada: datos, referencia, clave y TODO 1 a 4**. No genera salidas del pipeline ni muestra secretos.

Realiza ahora el recorrido de [REPASO_LAB1.md](REPASO_LAB1.md) para entender la base resuelta. No necesitas escribir funciones en ese repaso. Si ya conoces el Laboratorio 1, puedes revisar sus explicaciones sin repetir la ejecución. Después continúa con la sección 5.

## 5 Identifica tu trabajo en lab2.py

Abre `lab2.py`. La estructura de la auditoría está implementada. Sustituye el `raise NotImplementedError(...)` **solo dentro de la función que estés completando**. Conserva los nombres y parámetros. Guarda antes de probar.

| Orden | Función | Qué debes desarrollar |
| --- | --- | --- |
| TODO 5 | registrar_evento | Anexar un evento JSON por línea |
| TODO 6 | comprobar_minimizacion | Verificar el esquema mínimo del resumen |
| TODO 7 | comprobar_trazabilidad | Verificar la estructura y correlación de los eventos |

Los comprobadores no incluyen implementaciones de estas tres funciones. Sus archivos temporales representan entradas y resultados de prueba, no evidencias de tu auditoría real.

## 6 Completa TODO 5 Registro de eventos

Función: `registrar_evento(ruta, run_id, rol, operacion, resultado)`.

Debes abrir la ruta recibida para **anexar**, con codificación UTF-8. Cada llamada escribe un objeto JSON completo seguido de un salto de línea. No sobrescribas eventos anteriores.

El objeto debe tener exactamente estos campos, con valores de texto no vacíos:

| Campo | Valor que debes registrar |
| --- | --- |
| run_id | Identificador recibido |
| fecha_utc | Fecha actual con datetime.now(timezone.utc).isoformat() |
| rol | Rol recibido |
| operacion | Operación recibida |
| resultado | Resultado recibido |

Puedes usar `json.dumps` o `json.dump`. No agregues claves, tokens, nombres, correos o campos adicionales. La función registra el evento recibido; no debe decidir si una operación tiene permiso ni ejecutar el pipeline.

Guarda y ejecuta **solo esta etapa**:

```text
python comprobar_lab2.py --todo 5
```

Esperado: **TODO 5 OK: tres eventos anexados con campos exactos y fecha UTC.** Si la función sigue sin modificarse, verás **PENDIENTE: TODO 5**. Ese mensaje no significa que la etapa haya pasado.

## 7 Completa TODO 6 Minimización del resumen

Función: `comprobar_minimizacion(ruta)`.

Devuelve el booleano `True` únicamente si:

1. Puedes leer el CSV como UTF-8.
2. Los encabezados son exactamente `ciudad` y `total_ventas`, en ese orden.
3. Existe al menos una fila de datos.
4. Las filas están completas, sin columnas adicionales. `csv.DictReader` representa valores faltantes con `None` y columnas adicionales con una clave `None`; comprueba esas condiciones.

Un archivo ausente, ilegible, vacío o con formato/esquema inválido debe devolver **False**, no terminar con una excepción de lectura esperada ni dar éxito. No necesitas comprobar importes o totales comerciales aquí; ese control es diferente.

Usa `csv.DictReader` y considera errores esperados de lectura, codificación o CSV. Evita un `except` que convierta cualquier problema en `True` o esconda que una función sigue pendiente.

```text
python comprobar_lab2.py --todo 6
```

Esperado: **TODO 6 OK: resumen valido aceptado y ocho casos invalidos rechazados.** Esta etapa usa sus propios CSV temporales; **no necesita TODO 5 ni TODO 7 completos**.

## 8 Completa TODO 7 Trazabilidad de la ejecución

Función: `comprobar_trazabilidad(ruta, run_id)`.

Lee el archivo JSONL como UTF-8. Cada línea debe contener un objeto JSON con los mismos cinco campos exactos que escribiste en TODO 5. Todos sus valores deben ser `str` no vacíos ni compuestos solo por espacios.

Comprueba además que:

- Cada evento tenga el `run_id` recibido.
- `fecha_utc` se pueda interpretar como fecha ISO, tenga zona horaria y su desplazamiento sea UTC, es decir, cero. Puedes usar `datetime.fromisoformat`, `tzinfo` y `utcoffset()`.
- Existan los tres eventos de la ejecución válida que aparecen en la tabla siguiente. El orden no es un requisito adicional de esta comprobación.

| Rol | operacion | resultado |
| --- | --- | --- |
| operador | ejecutar | PERMITIDO |
| operador | pipeline | COMPLETADO |
| analista | ejecutar | DENEGADO |

El tercer evento representa un intento simulado por el orquestador. No atribuyas esa acción a una persona real autenticada.

Devuelve `False` si falta el archivo, está vacío, no es UTF-8, tiene JSON inválido, una línea no es un objeto, aparecen campos extra o faltantes, valores inválidos, una fecha sin UTC, otro run_id o falta un evento requerido. Devuelve `True` solo si la traza cumple todo. No basta con comprobar que el archivo existe.

**Esta función lee y valida; no llama a registrar_evento ni modifica el registro.** Guarda y prueba:

```text
python comprobar_lab2.py --todo 7
```

Esperado: **TODO 7 OK: traza valida aceptada y catorce casos invalidos rechazados.** El comprobador crea una traza de prueba independiente; **puedes verificar TODO 7 aunque TODO 5 o TODO 6 sigan pendientes**.

## 9 Ejecuta todas las comprobaciones aisladas

Después de aprobar cada etapa:

```text
python comprobar_lab2.py
```

Debe mostrar los tres mensajes OK y terminar con **TODO 5, 6 y 7 verificados. Continua con la auditoria completa.** Sin `--todo`, el orden es 5, 6 y 7; se detiene en el primer pendiente o fallo.

Una etapa aprobada no valida las otras. Código de salida 0: pruebas seleccionadas satisfactorias; 2: TODO pendiente o argumentos inválidos; 1: fallo o problema de entrada. Las pruebas negativas del comprobador son satisfactorias cuando la función rechaza lo que debe rechazar.

## 10 Ejecuta una auditoría válida

Con los tres TODO completos, el entorno activo y DATAOPS_KEY cargada:

```text
python lab2.py ejecutar --rol operador
```

La consola muestra **Reporte generado:** y una ruta. Cada llamada crea una carpeta nueva `ejecuciones/RUN_ID`, sin sobrescribir las ejecuciones anteriores.

| Ruta dentro de esa carpeta | Contenido |
| --- | --- |
| eventos.jsonl | Eventos operativos sin datos personales o secretos |
| reporte.json | Identificador, fecha, rol, hash y resultados de controles |
| salidas/detalle_protegido.csv | Los 12 pedidos con nombre y correo cifrados |
| salidas/resumen.csv | Tres ciudades y ventas confirmadas |

Consulta el reporte como auditor:

```text
python lab2.py consultar --rol auditor --reporte ejecuciones/RUN_ID/reporte.json
```

**Sustituye RUN_ID por el identificador real de la ruta recién generada.** No escribas RUN_ID literalmente. Si una ruta contiene espacios, escríbela entre comillas.

Debes observar estos cinco controles en estado **SATISFACTORIO**:

| Control | Evidencia o comprobación |
| --- | --- |
| INTEGRIDAD | Coincidencia con referencia.sha256 y hash_entrada en el reporte |
| CIFRADO | Nombre y correo se recuperan y coinciden con el original |
| MINIMIZACION | Resumen con esquema mínimo y filas |
| ACCESO_DENEGADO | Analista no puede ejecutar y se registra DENEGADO |
| TRAZABILIDAD | Eventos completos con el mismo run_id y fecha UTC |

El resumen debe contener Merida 4000.00, Puebla 2500.00 y Villahermosa 4250.00. Total de control: 10750.00. Los tokens pueden variar y no se comparan literalmente.

`SATISFACTORIO` indica que la comprobación se ejecutó y pasó. `FALLIDO` indica un error o incumplimiento detectado. `NO_EVALUADO` indica que un pendiente o bloqueo impidió comprobar. **El comando ejecutar puede terminar con código 0 aunque el reporte contenga fallos; interpreta los estados del JSON.**

## 11 Simula fallos y explica el resultado

Ejecuta cada escenario por separado. Antes de ejecutar, predice qué control actuará. Conserva el reporte y su run_id real.

### A Entrada alterada

```text
python lab2.py ejecutar --rol operador --entrada datos/pedidos_prueba_parte1.csv
```

Esperado: INTEGRIDAD y EJECUCION **FALLIDO**; CIFRADO, MINIMIZACION, ACCESO_DENEGADO y TRAZABILIDAD **NO_EVALUADO**. Se conserva el reporte, pero no existe la subcarpeta `salidas` de esta ejecución. No actualices la referencia para aceptar la copia.

### B Rol sin permiso para ejecutar

```text
python lab2.py ejecutar --rol analista
```

Esperado: evento ejecutar **DENEGADO**, AUTORIZACION_INICIAL y EJECUCION **FALLIDO**, los cinco controles previstos **NO_EVALUADO** y ninguna salida del pipeline. No declares verificada la integridad de un archivo que no llegó a procesarse.

### C Consulta sin permiso

Usa la ruta real de un reporte válido:

```text
python lab2.py consultar --rol analista --reporte ejecuciones/RUN_ID/reporte.json
```

Esperado: **PermissionError** antes de mostrar el reporte. El código puede mostrar el traceback. Esta consulta no crea un nuevo run_id ni registra el intento; reconoce ese límite al explicar la evidencia.

### D Calidad de las comprobaciones

```text
python comprobar_lab2.py --todo 6
python comprobar_lab2.py --todo 7
```

Ambas pruebas deben aceptar sus casos válidos y rechazar sus casos inválidos. Son pruebas en archivos temporales. Si haces cambios manuales, utiliza copias; no edites las evidencias originales. Corregir una función no cambia los reportes anteriores: ejecuta otra auditoría y conserva su nuevo run_id.

## 12 Registra tus evidencias y conclusiones

Completa `evidencias_lab2.md` con lo observado realmente: resultados por etapa, run_id válido, controles, rutas y resultados de A, B y C. Explica qué ocurrió, qué control actuó, dónde está la evidencia y qué corregirías. Registra también si algo no funcionó.

No incluyas `.secrets/fernet.key`, `.venv/`, tokens ni datos recuperados en capturas o entregas. Conserva localmente los archivos originales necesarios para reproducir tu práctica.

El laboratorio evalúa controles técnicos concretos. No certifica cumplimiento integral de GDPR o CCPA. El registro y el reporte son archivos locales modificables; los roles de consola no prueban la identidad real del ejecutor. La minimización verifica el esquema del resumen de este caso, no toda la organización. En producción se necesitan decisiones adicionales sobre acceso, custodia, conservación y atención de derechos.

## 13 Si algo falla

| Mensaje o síntoma | Acción |
| --- | --- |
| PENDIENTE TODO 5, 6 o 7 | Implementa esa función, guarda y repite su comando --todo. |
| ModuleNotFoundError | Usa el intérprete del entorno virtual y coloca lab1.py y lab2.py juntos. |
| Falta DATAOPS_KEY | Carga la clave original en la terminal actual. |
| Clave inválida o InvalidToken | Revisa la clave original y el token; no regeneres claves para recuperar datos. |
| El original no coincide | Detén el procesamiento y revisa el origen; no recalcules la referencia. |
| El destino de repaso ya existe | Usa otro destino nuevo en todas las operaciones relacionadas de lab1.py. |
| NO_EVALUADO | Revisa el primer pendiente o bloqueo; no lo interpretes como aprobación. |
| La etapa 6 o 7 lanza una excepción con un archivo inválido | Revisa el contrato: esos casos deben devolver False. |

## Referencias de consulta técnica

- [json de Python 3.12](https://docs.python.org/3.12/library/json.html)
- [csv de Python 3.12](https://docs.python.org/3.12/library/csv.html)
- [datetime de Python 3.12](https://docs.python.org/3.12/library/datetime.html)
- [hashlib de Python 3.12](https://docs.python.org/3.12/library/hashlib.html)
- [Fernet](https://cryptography.io/en/stable/fernet/)
