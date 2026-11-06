# Comercial Nova · Laboratorio 2 versión 2.1: evidencias y auditoría técnica del pipeline

Solución del **Laboratorio 2 del paquete 2.1 (cumplimiento normativo)**, trabajo final del curso de Seguridad en DataOps con Python sobre el caso ficticio Comercial Nova. El repositorio parte de la base resuelta de la sesión anterior (hashing, autorización, cifrado y recuperación) y añade lo que faltaba para responder a una auditoría: un registro estructurado de eventos, la verificación del esquema mínimo del resumen, la verificación de la traza de cada ejecución y un reporte con el estado de cinco controles.

## Objetivo del laboratorio

Que cada ejecución del pipeline deje evidencia suficiente para responder cuatro preguntas: qué entrada se procesó, qué operación se permitió o denegó, qué control se comprobó y dónde está la evidencia. La auditoría aplica este orden fijo:

1. **Autorización**: el rol debe tener la operación `ejecutar`; se registra `PERMITIDO` o `DENEGADO`.
2. **Integridad**: la huella de la entrada debe coincidir con `referencia.sha256`.
3. **Pipeline**: validación, cifrado de nombre y correo y escritura en `ejecuciones/RUN_ID/salidas`; se registra `COMPLETADO`.
4. **Cifrado**: cada token del detalle se descifra al valor original.
5. **Minimización**: el resumen solo contiene `ciudad` y `total_ventas`.
6. **Acceso denegado**: un intento simulado del analista se rechaza y se registra `DENEGADO`.
7. **Trazabilidad**: los eventos son completos, comparten el `run_id` y tienen fecha UTC.

Los TODO 5, 6 y 7 de `lab2.py` (`registrar_evento`, `comprobar_minimizacion` y `comprobar_trazabilidad`) están implementados. Duración prevista: 60 minutos de laboratorio y 25 de simulación de fallos.

## Estructura del repositorio

| Ruta | Contenido |
| --- | --- |
| `lab2.py` | Auditoría orientada a objetos con los TODO 5 a 7 resueltos y la CLI `ejecutar` y `consultar`. |
| `lab1.py` | Pipeline de la sesión anterior con el mismo diseño de clases y la CLI de repaso. |
| `preparar.py` | `PreparadorEntorno`: genera dataset, referencia y clave sin mostrarlos. |
| `comprobar_1a.py` | Comprobador de TODO 1, 3 y 4; admite `--todo` y `--base <carpeta>`. |
| `comprobar_preparacion_lab2.py` | Verifica datos, referencia, clave y TODO 1 a 4; admite `--base <carpeta>`. |
| `comprobar_lab2.py` | Comprobador independiente de TODO 5, 6 y 7 con archivos temporales; admite `--todo`. |
| `pruebas/` | Pruebas pytest con entornos aislados en `tmp_path`. |
| `pytest.ini` | Convenciones de nombres de pytest en español. |
| `evidencias_lab2.md` | Resultados reales observados, escenarios A a D y conclusiones. |
| `ejecuciones/89ae7a5b6f494eeeb9531101d20524f1/` | Ejecución válida versionada: eventos, reporte y resumen de totales. |
| `ejecuciones/c1b45f71…`, `5617740c…`, `a3dc4643…` | Escenarios A y B y la prueba sin clave citados en las evidencias: eventos y reporte. |
| `GUIA_PARTICIPANTE.md`, `REPASO_LAB1.md` | Guías originales del curso, conservadas sin cambios. |
| `.github/workflows/pruebas.yml` | Integración continua en Ubuntu y Windows. |
| `.github/dependabot.yml` | Actualización semanal de las acciones fijadas por SHA y de las dependencias de `requirements.txt`. |
| `requirements.txt` | `cryptography==50.0.2` y `pytest==9.1.1`. |

Las guías `GUIA_PARTICIPANTE.md` y `REPASO_LAB1.md` describen el material del curso con los TODO 5 a 7 pendientes; la solución está en los archivos `.py`.

No se versionan `datos/`, `.secrets/`, `referencia.sha256`, `.venv/`, `salidas/`, el resto de `ejecuciones/` ni ningún `detalle_protegido.csv`: la guía pide no entregar tokens.

## Requisitos

- Python 3.12 con `venv` y `pip`.
- Conexión a Internet para instalar dependencias.
- Ningún servicio de nube ni base de datos.

## Instalación

En Windows PowerShell:

```text
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, no cambies las políticas del equipo. Instala con el intérprete del entorno y sustituye python por `.\.venv\Scripts\python.exe` en los comandos posteriores.

```text
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En WSL o Linux:

```text
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Elige una sola alternativa; no mezcles un entorno virtual de Windows con WSL.

## Preparar el entorno y cargar la clave

```text
python preparar.py
```

Resultado esperado: `Dataset, referencia y clave creados sin mostrarlos`. Si el entorno ya existe, el programa termina con `FileExistsError: Entorno existente; revisar antes de recrear` y no reemplaza nada. Se ejecuta una sola vez: al volver otro día basta con activar el entorno y cargar de nuevo la clave.

Carga la clave en la misma terminal que ejecutará Python. En PowerShell:

```text
$env:DATAOPS_KEY = (Get-Content .secrets/fernet.key -Raw).Trim()
```

En WSL o Linux:

```text
export DATAOPS_KEY="$(cat .secrets/fernet.key)"
```

No imprimas la clave ni la copies al código, a Git, a capturas o a evidencias.

## Orden exacto de comandos para reproducir

Verificación de la base y repaso del Laboratorio 1:

```text
python comprobar_1a.py --todo 1
python comprobar_preparacion_lab2.py
python lab1.py inspeccionar
python comprobar_1a.py
python lab1.py ejecutar --rol operador --destino salidas/repaso_lab1
python lab1.py resumen --rol analista --destino salidas/repaso_lab1
python lab1.py recuperar --rol operador --destino salidas/repaso_lab1
python lab1.py ejecutar --rol analista --destino salidas/repaso_denegada
python lab1.py ejecutar --rol operador --entrada datos/pedidos_prueba_parte1.csv --destino salidas/repaso_alterada
```

Comprobación de los TODO 5 a 7 y auditoría:

```text
python comprobar_lab2.py --todo 5
python comprobar_lab2.py --todo 6
python comprobar_lab2.py --todo 7
python comprobar_lab2.py
python lab2.py ejecutar --rol operador
python lab2.py consultar --rol auditor --reporte ejecuciones/RUN_ID/reporte.json
```

Sustituye `RUN_ID` por el identificador que imprime `ejecutar`. Escenarios de fallo de la sección 11 de la guía:

```text
python lab2.py ejecutar --rol operador --entrada datos/pedidos_prueba_parte1.csv
python lab2.py ejecutar --rol analista
python lab2.py consultar --rol analista --reporte ejecuciones/RUN_ID/reporte.json
python comprobar_lab2.py --todo 6
python comprobar_lab2.py --todo 7
```

Cada `ejecutar` crea una carpeta nueva, de modo que las ejecuciones versionadas no impiden repetir la auditoría en un clon nuevo. Su detalle con tokens no se publica y se cifró con la clave del autor; para consultar tu propio reporte usa el `RUN_ID` de tu ejecución.

## Matriz de roles

| Operación | Operador | Analista | Auditor |
| --- | --- | --- | --- |
| Ejecutar (`lab1.py` y `lab2.py`) | Sí | No | No |
| Resumen (`lab1.py`) | No | Sí | No |
| Recuperar (`lab1.py`) | Sí | No | No |
| Evidencias (`lab2.py consultar`) | No | No | Sí |

Un rol desconocido o una operación no listada se deniegan con `PermissionError`; el mensaje indica rol y operación, nunca datos personales. No hay permisos por defecto. El argumento `--rol` simula una identidad ya autenticada.

## Resultados esperados

| Comprobación | Resultado esperado |
| --- | --- |
| `comprobar_lab2.py` | Tres líneas `TODO n OK` y `TODO 5, 6 y 7 verificados. Continua con la auditoria completa.` |
| Auditoría válida | `Reporte generado:` con la ruta; INTEGRIDAD, CIFRADO, MINIMIZACION, ACCESO_DENEGADO y TRAZABILIDAD en `SATISFACTORIO` |
| `eventos.jsonl` | Tres eventos con el mismo `run_id`: operador ejecutar PERMITIDO, operador pipeline COMPLETADO, analista ejecutar DENEGADO |
| Salidas | 12 filas en `detalle_protegido.csv` y 3 ciudades en `resumen.csv` |
| Escenario A | INTEGRIDAD y EJECUCION `FALLIDO`; los otros cuatro `NO_EVALUADO`; sin subcarpeta `salidas` |
| Escenario B | AUTORIZACION_INICIAL y EJECUCION `FALLIDO`; los cinco previstos `NO_EVALUADO`; evento DENEGADO |
| Escenario C | `BLOQUEADO: PermissionError` con código 1, sin mostrar el reporte ni crear otro `run_id` |
| Consulta de otra ruta | `BLOQUEADO: ValueError` con código 1: `consultar` solo lee `ejecuciones/RUN_ID/reporte.json` |

| Ciudad | total_ventas |
| --- | --- |
| Merida | 4000.00 |
| Puebla | 2500.00 |
| Villahermosa | 4250.00 |
| Total de control | 10750.00 |

`ejecutar` termina con código 0 aunque el reporte contenga fallos: los estados se interpretan en el JSON. `SATISFACTORIO` indica que la comprobación se ejecutó y pasó, `FALLIDO` que detectó un error y `NO_EVALUADO` que un bloqueo impidió comprobarla. `comprobar_1a.py` y `comprobar_lab2.py` terminan con 0 si pasan, 1 ante un fallo y 2 ante un TODO pendiente o argumentos inválidos; `comprobar_preparacion_lab2.py` termina con 0 o con 1, y solo da 2 con argumentos inválidos.

## Pruebas automatizadas

```text
python -m pytest -q
```

Resultado actual: 225 pruebas superadas. Cada prueba crea su propio entorno en `tmp_path` con `PreparadorEntorno` e inyecta `DATAOPS_KEY` con `monkeypatch`, de modo que no dependen de `datos/`, `.secrets/`, `referencia.sha256` ni `ejecuciones/` del repositorio. Las pruebas de la CLI copian los scripts al entorno temporal para usar las rutas por omisión de la guía.

| Módulo | Pruebas | Qué cubre |
| --- | --- | --- |
| `prueba_registro_eventos.py` | 19 | Anexado sin sobrescribir, campos exactos, UTF-8, fecha UTC reciente, reloj inyectado, sin datos personales ni clave, valores vacíos rechazados. |
| `prueba_minimizacion.py` | 25 | Resumen válido, los ocho casos inválidos de la guía y otros (mayúsculas, valores vacíos, Latin-1, carpeta, comillas sin cerrar, campo mayor que el límite de `csv`, detalle). |
| `prueba_trazabilidad.py` | 41 | Traza válida, orden no exigido, sufijo Z, separador Unicode dentro de un valor, los catorce inválidos de la guía y otros (claves repetidas, tipos, zonas, línea en blanco); solo lectura. |
| `prueba_cifrado.py` | 8 | Detalle válido, campo en claro, token de otro valor, filas desordenadas o faltantes, otra clave y falta de clave. |
| `prueba_auditoria.py` | 35 | Cinco controles, reporte, carpeta, tres eventos, salidas y totales, escenarios A, B y C, rol en blanco, consulta limitada a `ejecuciones/RUN_ID/reporte.json`, falta de clave, entrada ausente, comprobaciones pendientes o rotas, no sobrescritura. |
| `prueba_interfaz_auditoria.py` | 15 | CLI de `lab2.py` por subprocess: `ejecutar`, escenarios A y B, falta de clave, `consultar` como auditor y otros roles, falta de `--reporte`, intento de leer la clave, reporte inexistente. |
| `prueba_comprobadores.py` | 20 | `comprobar_preparacion_lab2.py --base` y `comprobar_lab2.py` con la solución y con versiones de prueba pendientes, permisivas o que lanzan excepciones. |
| `prueba_control_acceso.py` | 19 | Las 12 combinaciones rol x operación, rol y operación desconocidos, mensajes sin datos personales. |
| `prueba_pipeline.py` | 22 | Caso autorizado de `lab1.py`, detalle cifrado, resumen, consultas por rol, InvalidToken, bloqueos sin escritura, fila con columnas de más, orden de controles. |
| `prueba_interfaz.py` | 14 | CLI de `lab1.py` (`inspeccionar`, permitidas y bloqueos) y `comprobar_1a.py --base` con `--todo`. |
| `prueba_preparar.py` | 7 | `PreparadorEntorno` (tres archivos, 12 filas, contrato, no reemplaza), huella y cifrado. |

## Diseño de clases

| Clase | Módulo | Responsabilidad |
| --- | --- | --- |
| `RegistradorEventos` | `lab2.py` | Anexar eventos JSONL en UTF-8 con los cinco campos exactos; reloj inyectable. |
| `VerificadorMinimizacion` | `lab2.py` | Esquema mínimo del resumen; cualquier error de lectura devuelve False. |
| `VerificadorTrazabilidad` | `lab2.py` | Estructura, valores, `run_id`, fecha UTC y eventos requeridos; solo lectura. |
| `VerificadorCifrado` | `lab2.py` | Correspondencia fila a fila y recuperación de cada token. |
| `ReporteAuditoria` | `lab2.py` | Controles con estado, evidencia y acción; huella verificada. |
| `AuditorNova` | `lab2.py` | Orden de controles, carpeta `ejecuciones/RUN_ID`, reporte y consulta del auditor. |
| `InterfazAuditoria` | `lab2.py` | CLI `ejecutar` y `consultar` con `argparse`. |
| `CalculadoraHuella` | `lab1.py` | SHA-256 hexadecimal leyendo por bloques de 65536 bytes. |
| `CifradorCampos` | `lab1.py` | Cifrar y descifrar texto con Fernet; carga la clave desde `DATAOPS_KEY`. |
| `ControlAcceso` | `lab1.py` | Matriz de permisos; deniega roles y operaciones no listados. |
| `ValidadorPedidos` | `lab1.py` | Contrato de columnas, dataset no vacío, identificadores únicos, importes y estados. |
| `VerificadorIntegridad` | `lab1.py` | Comparar la huella de la entrada con la referencia confiable. |
| `EscritorCsv` | `lab1.py` | Escribir CSV UTF-8 con encabezado. |
| `PipelineNova` | `lab1.py` | Orquestar permiso, integridad, validación, cifrado y escritura. |
| `InterfazLinea` | `lab1.py` | CLI de repaso con traducción de excepciones a códigos de salida. |
| `PreparadorEntorno` | `preparar.py` | Generar dataset, referencia y clave sin reemplazar un entorno existente. |
| `ComprobadorLaboratorio1A` | `comprobar_1a.py` | Etapas TODO 1, 3 y 4 sobre la carpeta base elegida. |
| `ComprobadorPreparacion` | `comprobar_preparacion_lab2.py` | Datos, referencia, clave, cifrado y matriz de permisos. |
| `ComprobadorLaboratorio2` | `comprobar_lab2.py` | Etapas TODO 5, 6 y 7 con archivos temporales propios. |

Las funciones del material conservan nombres, parámetros y contratos y delegan en estas clases: en `lab2.py`, `registrar_evento`, `comprobar_minimizacion`, `comprobar_trazabilidad`, `comprobar_cifrado`, `auditar` y `main`; en `lab1.py`, `calcular_hash`, `autorizar`, `cifrar`, `descifrar`, `cargar_cifrador`, `leer_pedidos`, `verificar_integridad`, `escribir_csv`, `ejecutar`, `consultar_resumen`, `recuperar_muestra` y `main`. Los comprobadores no contienen las soluciones de los TODO.

## Riesgos, controles y pruebas

| Riesgo | Control | Prueba que lo demuestra |
| --- | --- | --- |
| No poder reconstruir qué ocurrió en una ejecución | Eventos JSONL con `run_id` y fecha UTC | `prueba_tres_eventos` y `prueba_anexa_tres_eventos` |
| Evidencia sobrescrita o perdida | Anexado y carpeta nueva por ejecución | `prueba_no_sobrescribe_eventos_previos` y `prueba_dos_ejecuciones_independientes` |
| Datos personales o secretos en la evidencia | Eventos con cinco campos exactos; consola solo con rutas | `prueba_sin_datos_personales_ni_clave` y `prueba_consola_sin_secretos` |
| Resumen que expone columnas de más | `VerificadorMinimizacion` | `prueba_contenido_invalido` (13 casos) y `prueba_detalle_protegido_rechazado` |
| Traza incompleta, mezclada o con fechas ambiguas | `VerificadorTrazabilidad` | `prueba_variante_invalida` (20 casos) y `prueba_contenido_invalido` (7 casos) |
| Un error de lectura tomado por aprobación | Todo error esperado devuelve False; solo `True` exacto aprueba | `prueba_no_utf8`, `prueba_archivo_ausente` y `prueba_resultado_no_booleano` |
| Procesar una entrada modificada | Integridad antes del pipeline | Escenario A: `prueba_estados` y `prueba_sin_salidas_ni_huella` |
| Un rol ejecuta o lee evidencias que no le corresponden | `ControlAcceso` con denegación por defecto | Escenarios B y C, también por CLI |
| Usar `consultar` para leer la clave o los datos | Solo se aceptan rutas `ejecuciones/RUN_ID/reporte.json` | `prueba_solo_reportes_de_ejecuciones` y `prueba_no_lee_la_clave` |
| Declarar verificado lo que no se comprobó | `NO_EVALUADO` para lo bloqueado o pendiente | `prueba_comprobacion_pendiente` y escenarios A y B |

## Si algo falla

| Señal | Primera revisión |
| --- | --- |
| ModuleNotFoundError | Instala requirements.txt con el intérprete del entorno virtual y deja lab1.py y lab2.py juntos. |
| PENDIENTE: TODO n | Implementa esa función, guarda y repite su comando `--todo`. |
| Falta DATAOPS_KEY | Carga la clave original en la misma terminal que ejecuta Python. |
| InvalidToken o clave inválida | Comprueba que usas la clave original; no regeneres claves para recuperar salidas. |
| El original no coincide | Detén el procesamiento y revisa su origen; no recalcules la referencia. |
| NO_EVALUADO en el reporte | Revisa el primer bloqueo o pendiente; no lo interpretes como aprobación. |
| El destino de repaso ya existe | Usa otro destino nuevo en todas las operaciones relacionadas de `lab1.py`. |
| FileExistsError en `preparar.py` | El entorno ya está preparado: carga su clave y continúa sin repetir la preparación. |

## Límites del laboratorio frente a producción

El laboratorio produce evidencias técnicas de controles concretos y no certifica cumplimiento integral de GDPR o CCPA. El registro y el reporte son archivos locales modificables, el original permanece legible y el cifrado no anonimiza los identificadores restantes. Los roles se simulan con `--rol`, el evento DENEGADO de ACCESO_DENEGADO lo genera el propio orquestador y la consulta denegada del escenario C no queda registrada. En producción haría falta:

- Registro de auditoría inalterable (solo anexado, firmado o en un servicio externo) con conservación definida.
- Identidad verificada y permisos aplicados por el sistema, también para cada consulta de evidencias.
- Custodia y rotación de claves en un gestor de secretos y referencia publicada con aprobación separada.
- Decisiones de minimización, conservación y atención de derechos para toda la organización, no solo para este resumen.

## Relación con los laboratorios anteriores

Este repositorio continúa el [Laboratorio 1 (tramo 1A: protección e integridad)](https://github.com/Jeshua-Romero-Guadarrama/bsg-seguridad-en-dataops-con-python-laboratorio-1) y el [Laboratorio 2 (tramo 1B: autorización e integración)](https://github.com/Jeshua-Romero-Guadarrama/bsg-seguridad-en-dataops-con-python-laboratorio-2). `lab1.py`, `preparar.py` y `comprobar_1a.py` reutilizan el diseño de clases de esos repositorios, adaptado al paquete 2.1 (acción `inspeccionar`, comprobador por etapas con `--todo`), y `lab2.py` añade el registro de eventos, la minimización, la trazabilidad y la auditoría con el mismo estilo.
