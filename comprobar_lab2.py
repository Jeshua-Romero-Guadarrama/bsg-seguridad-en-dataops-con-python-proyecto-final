"""Comprobador del Laboratorio 2 (paquete 2.1), independiente por TODO.

No contiene las soluciones de los TODO: cada etapa crea sus propios archivos
temporales y llama a la función correspondiente de lab2.py. TODO 5 anexa tres
eventos y revisa campos, valores y fecha UTC; TODO 6 acepta un resumen válido
y rechaza ocho casos inválidos; TODO 7 acepta una traza válida y rechaza
catorce casos inválidos. Una etapa aprobada no valida las otras.

Uso:
    python comprobar_lab2.py [--todo {5,6,7}]

Sin --todo prueba 5, 6 y 7 en ese orden y se detiene en el primer pendiente
o fallo. No admite --base: nunca lee datos/, .secrets/ ni ejecuciones/.

Códigos de salida: 0 si las etapas seleccionadas pasan, 1 si hay un fallo o
un problema de entrada y 2 si un TODO sigue pendiente o los argumentos no
son válidos.
"""
import argparse
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

RUN_ID_PRUEBA = 'prueba_aislada'
CAMPOS_EVENTO = {'run_id', 'fecha_utc', 'rol', 'operacion', 'resultado'}
EVENTOS_VALIDOS = [
    ('operador', 'ejecutar', 'PERMITIDO'),
    ('operador', 'pipeline', 'COMPLETADO'),
    ('analista', 'ejecutar', 'DENEGADO'),
]
RESUMENES_INVALIDOS = [
    'ciudad,total_ventas,correo\nMerida,4000.00,cliente@example.com\n',
    'ciudad,total_ventas\n',
    'total_ventas,ciudad\n4000.00,Merida\n',
    '',
    'ciudad,total_ventas\nMerida\n',
    'ciudad,total_ventas\nMerida,4000.00,extra\n',
]
# Campo y valor que invalidan el primer evento de una traza correcta.
ALTERACIONES_TRAZA = [
    ('run_id', 'otra_ejecucion'),
    ('correo', 'cliente@example.com'),
    ('fecha_utc', '2026-10-26T10:00:00'),
    ('fecha_utc', '2026-10-26T10:00:00+01:00'),
    ('rol', '   '),
    ('resultado', None),
]
CONTENIDOS_INVALIDOS = ['no_es_json\n', '', '[]\n', 'null\n']
BYTES_NO_UTF8 = b'\xff\xfe\xfa'


def exigir(condicion, mensaje):
    """Lanza AssertionError con el mensaje si la condición no se cumple."""
    if not condicion:
        raise AssertionError(mensaje)


class ComprobadorLaboratorio2:
    """Ejecuta las etapas TODO 5, 6 y 7 en una carpeta temporal."""

    def __init__(self, lab2, raiz):
        """Recibe el módulo a comprobar y la carpeta de archivos temporales.

        Argumentos:
            lab2: módulo lab2 ya importado.
            raiz: carpeta temporal donde se escriben los casos de prueba.
        """
        self.lab2 = lab2
        self.raiz = Path(raiz)
        self.en_curso = None

    def probar_5(self):
        """TODO 5: tres eventos anexados con campos exactos y fecha UTC."""
        ruta = self.raiz / 'eventos_todo5.jsonl'
        for rol, operacion, resultado in EVENTOS_VALIDOS:
            self.lab2.registrar_evento(ruta, RUN_ID_PRUEBA, rol, operacion,
                                       resultado)
        contenido = ruta.read_text(encoding='utf-8')
        lineas = contenido.splitlines()
        exigir(len(lineas) == 3,
               'TODO 5: debes anexar tres eventos sin sobrescribir')
        exigir(contenido.endswith('\n'),
               'TODO 5: termina cada objeto JSON con un salto de linea')
        for linea, triple in zip(lineas, EVENTOS_VALIDOS):
            evento = json.loads(linea)
            exigir(isinstance(evento, dict) and set(evento) == CAMPOS_EVENTO,
                   'TODO 5: cada linea debe tener los cinco campos exactos')
            exigir(all(isinstance(v, str) and v.strip()
                       for v in evento.values()),
                   'TODO 5: los valores deben ser textos no vacios')
            exigir(evento['run_id'] == RUN_ID_PRUEBA,
                   'TODO 5: conserva el run_id recibido')
            exigir((evento['rol'], evento['operacion'], evento['resultado'])
                   == triple,
                   'TODO 5: conserva los valores de la operacion recibida')
            fecha = datetime.fromisoformat(evento['fecha_utc'])
            exigir(fecha.tzinfo is not None
                   and fecha.utcoffset() == timedelta(0),
                   'TODO 5: fecha ISO con zona UTC')
            segundos = (datetime.now(timezone.utc) - fecha).total_seconds()
            exigir(abs(segundos) < 120,
                   'TODO 5: genera la fecha actual, no una fecha fija')
        print('TODO 5 OK: tres eventos anexados con campos exactos y fecha UTC.')

    def probar_6(self):
        """TODO 6: resumen válido aceptado y ocho casos inválidos rechazados.

        Usa datos propios: no depende de registrar_evento ni de TODO 7.
        """
        ruta = self.raiz / 'resumen_todo6.csv'
        ruta.write_text('ciudad,total_ventas\nMerida,4000.00\n',
                        encoding='utf-8')
        exigir(self.lab2.comprobar_minimizacion(ruta) is True,
               'TODO 6: el resumen valido debe devolver True')
        for contenido in RESUMENES_INVALIDOS:
            ruta.write_text(contenido, encoding='utf-8')
            exigir(self.lab2.comprobar_minimizacion(ruta) is False,
                   'TODO 6: rechaza encabezados distintos, CSV vacio o '
                   'filas incompletas')
        ruta.write_bytes(BYTES_NO_UTF8)
        exigir(self.lab2.comprobar_minimizacion(ruta) is False,
               'TODO 6: un archivo que no puede leerse como UTF-8 devuelve False')
        exigir(self.lab2.comprobar_minimizacion(self.raiz / 'ausente.csv')
               is False, 'TODO 6: un archivo ausente debe devolver False')
        print('TODO 6 OK: resumen valido aceptado y ocho casos invalidos '
              'rechazados.')

    @staticmethod
    def traza_valida():
        """Devuelve los tres eventos de una ejecución válida con fecha actual."""
        fecha = datetime.now(timezone.utc).isoformat()
        return [
            {'run_id': RUN_ID_PRUEBA, 'fecha_utc': fecha, 'rol': rol,
             'operacion': operacion, 'resultado': resultado}
            for rol, operacion, resultado in EVENTOS_VALIDOS
        ]

    @staticmethod
    def variantes_invalidas(filas):
        """Construye las ocho trazas inválidas derivadas de una válida."""
        variantes = [filas[:-1]]
        for campo, valor in ALTERACIONES_TRAZA:
            copia = [dict(r) for r in filas]
            copia[0][campo] = valor
            variantes.append(copia)
        copia = [dict(r) for r in filas]
        del copia[0]['resultado']
        variantes.append(copia)
        return variantes

    def probar_7(self):
        """TODO 7: traza válida aceptada y catorce casos inválidos rechazados.

        Usa una traza propia: se prueba aunque TODO 5 y 6 sigan pendientes.
        """
        ruta = self.raiz / 'eventos_todo7.jsonl'

        def escribir(registros):
            ruta.write_text(''.join(json.dumps(r) + '\n' for r in registros),
                            encoding='utf-8')

        filas = self.traza_valida()
        escribir(filas)
        exigir(self.lab2.comprobar_trazabilidad(ruta, RUN_ID_PRUEBA) is True,
               'TODO 7: una traza completa y valida debe devolver True')
        for registros in self.variantes_invalidas(filas):
            escribir(registros)
            exigir(self.lab2.comprobar_trazabilidad(ruta, RUN_ID_PRUEBA)
                   is False,
                   'TODO 7: rechaza campos, valores, run_id o fecha invalidos '
                   'y eventos ausentes')
        for contenido in CONTENIDOS_INVALIDOS:
            ruta.write_text(contenido, encoding='utf-8')
            exigir(self.lab2.comprobar_trazabilidad(ruta, RUN_ID_PRUEBA)
                   is False,
                   'TODO 7: rechaza JSON invalido, contenido vacio u objetos '
                   'de otro tipo')
        ruta.write_bytes(BYTES_NO_UTF8)
        exigir(self.lab2.comprobar_trazabilidad(ruta, RUN_ID_PRUEBA) is False,
               'TODO 7: un archivo que no puede leerse como UTF-8 devuelve False')
        exigir(self.lab2.comprobar_trazabilidad(
            self.raiz / 'ausente.jsonl', RUN_ID_PRUEBA) is False,
            'TODO 7: un archivo ausente debe devolver False')
        print('TODO 7 OK: traza valida aceptada y catorce casos invalidos '
              'rechazados.')

    def comprobar(self, todo=None):
        """Ejecuta la etapa indicada o las tres en orden.

        Argumentos:
            todo: 5, 6 o 7; None ejecuta 5, 6 y 7.

        Lanza:
            NotImplementedError: si la función de la etapa sigue pendiente;
                self.en_curso indica qué etapa se estaba probando.
            AssertionError: si la función no cumple el contrato.
        """
        etapas = {5: self.probar_5, 6: self.probar_6, 7: self.probar_7}
        for numero in ([todo] if todo else [5, 6, 7]):
            self.en_curso = numero
            etapas[numero]()
        if todo:
            print(f'Etapa TODO {todo} verificada; no valida las otras funciones.')
        else:
            print('TODO 5, 6 y 7 verificados. Continua con la auditoria completa.')


def main(argv=None):
    """Interpreta --todo, ejecuta las etapas y devuelve el código de salida.

    Argumentos:
        argv: lista de argumentos; por omisión se usa sys.argv.

    Devuelve:
        0 si las etapas pasan, 1 si hay un fallo y 2 si falta un TODO.
    """
    parser = argparse.ArgumentParser(
        description='Comprobador del laboratorio 2 version 2.1, '
                    'independiente por TODO.')
    parser.add_argument('--todo', type=int, choices=[5, 6, 7],
                        help='Prueba solo la etapa seleccionada; sin opcion '
                             'prueba 5, 6 y 7')
    args = parser.parse_args(argv)
    numero = args.todo or 5
    try:
        import lab2
        exigir(Path(lab2.__file__).resolve().parent
               == Path(__file__).resolve().parent,
               'Coloca el comprobador junto a lab2.py y lab1.py')
        with tempfile.TemporaryDirectory(prefix='nova_lab2_') as temp:
            comprobador = ComprobadorLaboratorio2(lab2, temp)
            try:
                comprobador.comprobar(args.todo)
            finally:
                numero = comprobador.en_curso or numero
        return 0
    except NotImplementedError:
        print(f'PENDIENTE: TODO {numero}; implementa y guarda esa funcion en '
              'lab2.py', file=sys.stderr)
        return 2
    except AssertionError as exc:
        print(f'REVISAR: {exc}', file=sys.stderr)
        return 1
    except ModuleNotFoundError:
        print('REVISAR: faltan lab1.py, lab2.py o las dependencias; consulta '
              'README.md', file=sys.stderr)
        return 1
    except Exception as exc:
        # Solo el tipo de la excepcion: su texto podria contener datos.
        print(f'REVISAR TODO {numero}: {type(exc).__name__}; comprueba el '
              'contrato de errores', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
