# Repaso del Laboratorio 1 para comenzar la sesión 2

## El problema de Comercial Nova

Comercial Nova recibe pedidos en CSV. El equipo comercial necesita ventas confirmadas por ciudad, pero el detalle incluye nombres y correos. En la primera sesión se añadieron cifrado, verificación de integridad y permisos por operación.

El dataset es completamente ficticio: 12 pedidos, 11 clientes y tres ciudades. Hay nueve pedidos confirmados y tres cancelados. Los cancelados se conservan en el detalle y no suman ventas. Los correos utilizan example.com.

`preparar.py` contiene todos los registros; no necesitas descargar datos ni copiar código de otro documento. Genera `datos/pedidos.csv`, `referencia.sha256` y `.secrets/fernet.key`. Sigue primero la preparación de la guía principal.

## Lo que ya está implementado en lab1.py

| TODO de la sesión anterior | Función | Qué hace |
| --- | --- | --- |
| 1 resuelto | calcular_hash | Lee bytes por bloques y devuelve SHA-256 hexadecimal. |
| 2 resuelto | autorizar | Permite solo operaciones de PERMISOS; de lo contrario lanza PermissionError. |
| 3 resuelto | cifrar | Convierte texto UTF-8 en un token Fernet como texto ASCII. |
| 4 resuelto | descifrar | Recupera el texto UTF-8 original con la misma clave. |

No vuelvas a resolver estos TODO. Abre `lab1.py`, localiza las cuatro funciones y observa su implementación. `lab2.py` las importa para reutilizar el pipeline.

El recorrido completo es: autorización, integridad, validación del CSV, cifrado de nombre y correo, agregación de confirmados y escritura de salidas.

## Quién puede hacer cada operación

| Rol | Ejecutar | Consultar resumen | Recuperar muestra | Consultar evidencias |
| --- | --- | --- | --- | --- |
| operador | Sí | No | Sí | No |
| analista | No | Sí | No | No |
| auditor | No | No | No | Sí |
| desconocido | No | No | No | No |

La consulta de evidencias se incorpora mediante `lab2.py`. Los roles de consola simulan una identidad autenticada; no autentican personas ni aíslan archivos del sistema.

## Recorrido breve con el código resuelto

Con la clave cargada y el entorno preparado, ejecuta desde `comercial_nova`:

```text
python lab1.py inspeccionar
python comprobar_1a.py
python lab1.py ejecutar --rol operador --destino salidas/repaso_lab1
python lab1.py resumen --rol analista --destino salidas/repaso_lab1
python lab1.py recuperar --rol operador --destino salidas/repaso_lab1
```

La inspección muestra el primer registro ficticio y omite permisos intencionalmente; solo sirve como diagnóstico previo. El comprobador verifica hashing y cifrado y crea `datos/pedidos_prueba_parte1.csv`. El pipeline indica 12 filas procesadas. La recuperación muestra solo la primera muestra ficticia.

Si `salidas/repaso_lab1` ya existe, utiliza otro destino nuevo en las tres operaciones relacionadas; por ejemplo `salidas/repaso_lab1_2`. El programa no sobrescribe salidas anteriores. Este recorrido sirve para comprender la base incluida; no requiere archivos de la sesión anterior. Las salidas del repaso se guardan aparte de las auditorías del Laboratorio 2.

## Lo que deberías observar

| Archivo o prueba | Resultado |
| --- | --- |
| Original frente a referencia | Coincide |
| Copia alterada frente a referencia | No coincide |
| Cifrado y recuperación | El texto recuperado coincide |
| detalle_protegido.csv | 12 filas de datos, nombre y correo cifrados |
| resumen.csv | Solo ciudad y total_ventas, con tres filas de datos |

| Ciudad | total_ventas |
| --- | --- |
| Merida | 4000.00 |
| Puebla | 2500.00 |
| Villahermosa | 4250.00 |
| Total de control | 10750.00 |

Puedes comprobar los dos bloqueos básicos con destinos nuevos:

```text
python lab1.py ejecutar --rol analista --destino salidas/repaso_denegada
python lab1.py ejecutar --rol operador --entrada datos/pedidos_prueba_parte1.csv --destino salidas/repaso_alterada
```

Esperado: BLOQUEADO por permisos en el primero y por integridad en el segundo, sin crear sus destinos. No actualices la referencia para hacer pasar la copia alterada.

## Lo que añadiremos en esta sesión

El pipeline puede proteger y bloquear, pero falta un registro estructurado de lo ocurrido y un reporte de sus comprobaciones. En el Laboratorio 2 completarás el registro de eventos, la verificación del esquema mínimo del resumen y la verificación de trazabilidad. Continúa en `GUIA_PARTICIPANTE.md`.

El original permanece legible y requiere controles propios. Cifrar nombre y correo no anonimiza el resto de los identificadores. La referencia y la clave locales son simplificaciones del laboratorio.
