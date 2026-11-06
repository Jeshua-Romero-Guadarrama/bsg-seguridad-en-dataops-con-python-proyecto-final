# Evidencias del laboratorio 2 versión 2.1

Participante: Jeshua Romero Guadarrama  Fecha: 29-10-2026

No incluyas claves, tokens ni datos recuperados. Escribe los resultados observados, no solo los esperados.

Entorno: Windows 11, Python 3.12.10, cryptography 50.0.2, pytest 9.1.1, entorno virtual `.venv`. El entorno se preparó una sola vez con `python preparar.py` (`Dataset, referencia y clave creados sin mostrarlos`) y la clave se cargó en la terminal con `DATAOPS_KEY` desde `.secrets/fernet.key` sin mostrarla. Las fechas de los reportes están en UTC (madrugada del 30-10-2026 en UTC, noche del 29-10-2026 en hora local).

## Preparación y comprobaciones

Resultado de comprobar_preparacion_lab2.py: `Preparacion verificada: datos, referencia, clave y TODO 1 a 4` y `No se han creado salidas ni mostrado claves o datos personales` (código 0). Antes, `python comprobar_1a.py --todo 1` mostró `TODO 1 OK: original coincide True; copia alterada coincide False.` y creó `datos/pedidos_prueba_parte1.csv`, por lo que no apareció el aviso de copia ausente.

Resultado de comprobar_lab2.py --todo 5: `TODO 5 OK: tres eventos anexados con campos exactos y fecha UTC.` seguido de `Etapa TODO 5 verificada; no valida las otras funciones.` (código 0).

Resultado de comprobar_lab2.py --todo 6: `TODO 6 OK: resumen valido aceptado y ocho casos invalidos rechazados.` (código 0).

Resultado de comprobar_lab2.py --todo 7: `TODO 7 OK: traza valida aceptada y catorce casos invalidos rechazados.` (código 0).

Resultado de comprobar_lab2.py completo: los tres mensajes OK en orden y `TODO 5, 6 y 7 verificados. Continua con la auditoria completa.` (código 0).

## Auditoría válida

RUN_ID: `89ae7a5b6f494eeeb9531101d20524f1`

Ruta de reporte.json: `ejecuciones/89ae7a5b6f494eeeb9531101d20524f1/reporte.json`

Ruta de eventos.jsonl: `ejecuciones/89ae7a5b6f494eeeb9531101d20524f1/eventos.jsonl`

Comando: `python lab2.py ejecutar --rol operador`, que mostró solo `Reporte generado:` con la ruta (código 0). La consulta `python lab2.py consultar --rol auditor --reporte ejecuciones/89ae7a5b6f494eeeb9531101d20524f1/reporte.json` mostró el JSON completo (código 0): `rol_ejecutor` operador, `fecha_utc` 2026-10-30T03:29:43.754926+00:00 y `hash_entrada` igual al contenido de `referencia.sha256` (bd90a012…54d8f6c).

| Control | Estado observado | Evidencia concreta |
| --- | --- | --- |
| INTEGRIDAD | SATISFACTORIO | `hash_entrada` del reporte coincide con `referencia.sha256`. |
| CIFRADO | SATISFACTORIO | `salidas/detalle_protegido.csv`: los 12 nombres y correos son tokens que se descifran al original con la clave cargada. |
| MINIMIZACION | SATISFACTORIO | `salidas/resumen.csv`: encabezados exactos `ciudad,total_ventas` y tres filas completas. |
| ACCESO_DENEGADO | SATISFACTORIO | Tercera línea de `eventos.jsonl`: analista, ejecutar, DENEGADO. |
| TRAZABILIDAD | SATISFACTORIO | `eventos.jsonl`: tres eventos con los cinco campos, el mismo `run_id` y fecha con +00:00. |

Eventos observados, en orden: operador ejecutar PERMITIDO, operador pipeline COMPLETADO y analista ejecutar DENEGADO. Ninguna línea contiene correos, nombres, tokens ni la clave.

Filas de detalle: 12  Filas de resumen: 3

Totales por ciudad y total general: Merida 4000.00, Puebla 2500.00 y Villahermosa 4250.00; total de control 10750.00 (los tres pedidos cancelados no suman).

Esta ejecución se versiona en el repositorio con sus eventos, su reporte y el resumen de totales. El detalle con tokens, los datos originales y la clave no se versionan.

## Escenarios negativos

| Escenario | RUN_ID o ruta | Estados y resultado observados | Evidencia | Acción propuesta |
| --- | --- | --- | --- | --- |
| A Entrada alterada | `c1b45f718e9a4147bde763489c9a09da` | Código 0. INTEGRIDAD y EJECUCION FALLIDO (evidencia `ValueError`); CIFRADO, MINIMIZACION, ACCESO_DENEGADO y TRAZABILIDAD NO_EVALUADO; `hash_entrada` nulo. | `reporte.json` y `eventos.jsonl` con un solo evento (operador ejecutar PERMITIDO); no existe `salidas`. | Revisar el origen de `datos/pedidos_prueba_parte1.csv` y no procesarla; la referencia no se recalculó. |
| B Analista intenta ejecutar | `5617740cabb54c589c4669c3d6fdbd4c` | Código 0. AUTORIZACION_INICIAL y EJECUCION FALLIDO (evidencia `PermissionError`); los cinco controles previstos NO_EVALUADO; `hash_entrada` nulo. | `eventos.jsonl` con un único evento: analista ejecutar DENEGADO; no existe `salidas`. | Ejecutar con el rol operador; no declarar verificada la integridad de un archivo que no se procesó. |
| C Analista intenta consultar | No genera RUN_ID | `BLOQUEADO: PermissionError: Rol 'analista' sin permiso para 'evidencias'` (código 1); no se mostró el reporte. | `ejecuciones/` tenía 8 carpetas antes y 8 después en el equipo local; en el repositorio solo se versionan las cuatro citadas aquí. | Registrar también las consultas denegadas en un registro propio. |
| D Pruebas aisladas | Archivos temporales | `--todo 6`: resumen válido aceptado y ocho inválidos rechazados; `--todo 7`: traza válida aceptada y catorce inválidas rechazadas (código 0 en ambas). | Mensajes OK de `comprobar_lab2.py`; los archivos temporales se eliminan al terminar. | Mantener las pruebas negativas; `pytest` las amplía a 13 resúmenes y 27 trazas inválidas parametrizadas. |

¿Se crearon salidas del pipeline en A o B? No. Las carpetas de A y B solo contienen `eventos.jsonl` y `reporte.json`; el pipeline nunca llegó a crear la subcarpeta `salidas`.

¿Qué controles quedaron NO_EVALUADO y por qué? En A, CIFRADO, MINIMIZACION, ACCESO_DENEGADO y TRAZABILIDAD, porque el fallo de integridad detuvo la ejecución antes de generar salidas que comprobar. En B, los cinco controles previstos, porque la autorización inicial denegó la ejecución antes de leer la entrada. NO_EVALUADO no es una aprobación: indica que el bloqueo impidió comprobar.

### Pruebas complementarias observadas

| Prueba | Resultado observado |
| --- | --- |
| `consultar --rol auditor` sin `--reporte` | `lab2.py: error: consultar requiere --reporte RUTA` (código 2). |
| `consultar --rol operador` | `BLOQUEADO: PermissionError: Rol 'operador' sin permiso para 'evidencias'` (código 1). |
| `ejecutar` sin `DATAOPS_KEY` (`a3dc46435b9c41988a4c805245be259a`) | Código 0; INTEGRIDAD SATISFACTORIO con `hash_entrada`, EJECUCION FALLIDO por `ValueError` y los otros cuatro NO_EVALUADO; sin `salidas`. |
| Repaso de `lab1.py` en `salidas/repaso_lab1` | `inspeccionar` mostró el primer pedido ficticio; `comprobar_1a.py` verificó TODO 1, 3 y 4; `ejecutar` dio `Proceso terminado: 12 filas`, `resumen` las tres ciudades y `recuperar` la primera muestra ficticia (código 0). |
| Bloqueos del repaso | `BLOQUEADO: Rol 'analista' sin permiso para 'ejecutar'` y `BLOQUEADO: Integridad de entrada no valida` (código 1), sin crear `salidas/repaso_denegada` ni `salidas/repaso_alterada`; repetir sobre `salidas/repaso_lab1` dio `BLOQUEADO: [WinError 183]` sin sobrescribir. |
| `consultar --rol auditor --reporte .secrets/fernet.key` | `BLOQUEADO: ValueError: Solo se consultan reportes ejecuciones/RUN_ID/reporte.json` (código 1); la clave no se mostró. |
| Pruebas automatizadas | `python -m pytest -q`: 225 pruebas superadas (221 el 29-10-2026; el 05-11-2026 se añadieron cuatro casos límite y se repitió la suite). |

## Hallazgo y explicación

Qué ocurrió: con la copia alterada (un solo importe cambiado de 1850.00 a 1851.00) la auditoría terminó con código 0, pero el reporte de `c1b45f718e9a4147bde763489c9a09da` marcó INTEGRIDAD y EJECUCION como FALLIDO y dejó los otros cuatro controles en NO_EVALUADO. El código de salida no es el veredicto; lo son los estados del JSON.

Qué control actuó: la verificación de integridad con SHA-256 frente a `referencia.sha256`, después de registrar el evento PERMITIDO y antes de leer, cifrar o escribir nada. En el escenario B actuó antes la autorización inicial, que dejó el evento DENEGADO como única traza.

Dónde está la evidencia: en `ejecuciones/c1b45f718e9a4147bde763489c9a09da/reporte.json` (estados y acción `Revisar origen del archivo; no procesar`) y en `eventos.jsonl` de la misma carpeta, que muestra que la operación se permitió pero no llegó a `pipeline COMPLETADO`. La ausencia de `salidas` confirma que no se procesó la copia.

Qué corregirías: una corrección ya la apliqué durante la práctica. En el material, `consultar` leía cualquier ruta que recibiera, de modo que el auditor podía mostrar `.secrets/fernet.key` con `--reporte`. Ahora solo acepta `ejecuciones/RUN_ID/reporte.json` y responde `BLOQUEADO: ValueError` a cualquier otra ruta. Queda pendiente otra: el escenario C no deja rastro porque `consultar` no registra eventos; añadiría un registro de consultas (permitidas y denegadas) con `run_id` propio. También llevaría el registro a un almacén de solo anexado, porque hoy `eventos.jsonl` y `reporte.json` se pueden editar y una traza reescrita seguiría pasando TRAZABILIDAD si conserva la estructura.

Qué no demuestra este laboratorio: no certifica cumplimiento integral de GDPR o CCPA ni prueba la identidad de quien ejecuta, porque `--rol` es un texto declarado y el evento DENEGADO de ACCESO_DENEGADO lo simula el propio orquestador. La minimización verifica el esquema del resumen de este caso, no los importes ni el resto de la organización. El original sigue legible, los identificadores `pedido_id` y `cliente_id` quedan en claro y la clave y la referencia son archivos locales que requieren custodia propia.
