"""Evidencias y auditoría técnica del pipeline de Comercial Nova (Laboratorio 2).

Añade al pipeline resuelto de lab1.py un registro de eventos JSONL, la
verificación del esquema mínimo del resumen, la verificación de la traza de
cada ejecución y un reporte con el estado de cinco controles. Los TODO 5 a 7
(registrar_evento, comprobar_minimizacion y comprobar_trazabilidad) están
resueltos. Las funciones de módulo conservan los nombres, parámetros y
contratos del material del curso y delegan en las clases.

Cada auditoría crea una carpeta nueva ejecuciones/RUN_ID con eventos.jsonl,
reporte.json y, si el pipeline llegó a ejecutarse, la subcarpeta salidas. La
consola solo muestra rutas e identificadores; nunca claves, tokens, nombres ni
correos.

Uso:
    python lab2.py ejecutar [--rol ROL] [--entrada RUTA] [--referencia RUTA]
    python lab2.py consultar --rol auditor --reporte ejecuciones/RUN_ID/reporte.json
"""
import argparse
import csv
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import lab1

BASE = Path(__file__).resolve().parent
EJECUCIONES = BASE / 'ejecuciones'
CAMPOS_EVENTO = ('run_id', 'fecha_utc', 'rol', 'operacion', 'resultado')
ENCABEZADOS_RESUMEN = list(lab1.CAMPOS_RESUMEN)
# Rol, operacion y resultado de los tres eventos de una ejecucion valida.
EVENTOS_REQUERIDOS = frozenset({
    ('operador', 'ejecutar', 'PERMITIDO'),
    ('operador', 'pipeline', 'COMPLETADO'),
    ('analista', 'ejecutar', 'DENEGADO'),
})
CONTROLES_PREVISTOS = (
    'INTEGRIDAD', 'CIFRADO', 'MINIMIZACION', 'ACCESO_DENEGADO',
    'TRAZABILIDAD',
)
SATISFACTORIO = 'SATISFACTORIO'
FALLIDO = 'FALLIDO'
NO_EVALUADO = 'NO_EVALUADO'


def ahora_utc() -> datetime:
    """Devuelve la fecha y hora actuales con zona UTC."""
    return datetime.now(timezone.utc)


class RegistradorEventos:
    """Anexa eventos operativos a un archivo JSONL en UTF-8.

    Cada evento es un objeto JSON en una sola línea con los cinco campos de
    CAMPOS_EVENTO y nada más. El registrador no decide permisos ni ejecuta el
    pipeline: deja constancia de lo que recibe. Los mensajes de error nombran
    el campo, nunca su valor, para no copiar datos a la consola.
    """

    def __init__(self, reloj=None):
        """Recibe el reloj que fecha los eventos.

        Argumentos:
            reloj: función sin argumentos que devuelve un datetime con zona
                UTC; por omisión, la hora actual del sistema.
        """
        self.reloj = reloj or ahora_utc

    def registrar(self, ruta, run_id, rol, operacion, resultado) -> dict:
        """Anexa un evento al final del archivo sin tocar los anteriores.

        Argumentos:
            ruta: archivo JSONL; se crea si no existe.
            run_id: identificador de la ejecución.
            rol: rol que intentó la operación.
            operacion: operación intentada.
            resultado: resultado observado (PERMITIDO, DENEGADO, ...).

        Devuelve:
            Diccionario con el evento escrito.

        Lanza:
            ValueError: si algún valor no es un texto no vacío.
            OSError: si el archivo no puede abrirse para anexar.
        """
        evento = {
            'run_id': run_id,
            'fecha_utc': self.reloj().isoformat(),
            'rol': rol,
            'operacion': operacion,
            'resultado': resultado,
        }
        for campo, valor in evento.items():
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f'Valor de evento invalido: {campo}')
        linea = json.dumps(evento, ensure_ascii=False) + '\n'
        with Path(ruta).open('a', encoding='utf-8', newline='') as f:
            f.write(linea)
        return evento


class VerificadorMinimizacion:
    """Comprueba que el resumen solo exponga ciudad y total de ventas.

    Verifica el esquema, no los importes: encabezados exactos y en orden, al
    menos una fila y filas completas sin columnas adicionales. Cualquier
    archivo ausente, ilegible o con formato inválido se rechaza con False.
    """

    def __init__(self, encabezados=None):
        """Recibe los encabezados permitidos; por omisión, los del resumen.

        Argumentos:
            encabezados: lista ordenada de columnas permitidas.
        """
        self.encabezados = list(encabezados or ENCABEZADOS_RESUMEN)

    @staticmethod
    def _fila_completa(fila) -> bool:
        """Indica si una fila no tiene columnas extra ni valores vacíos.

        csv.DictReader guarda las columnas sobrantes bajo la clave None y
        rellena con None las que faltan.
        """
        if None in fila:
            return False
        return all(isinstance(valor, str) and valor.strip()
                   for valor in fila.values())

    def verificar(self, ruta) -> bool:
        """Devuelve True solo si el CSV cumple el esquema mínimo.

        Argumentos:
            ruta: CSV de resumen a revisar.

        Devuelve:
            True si el esquema es exacto y todas las filas están completas;
            False en cualquier otro caso, incluidos los errores de lectura.
        """
        try:
            with Path(ruta).open(encoding='utf-8', newline='') as f:
                lector = csv.DictReader(f)
                if lector.fieldnames != self.encabezados:
                    return False
                filas = list(lector)
        except (OSError, UnicodeDecodeError, csv.Error):
            return False
        return bool(filas) and all(self._fila_completa(f) for f in filas)


class VerificadorTrazabilidad:
    """Comprueba la estructura y la correlación de la traza de una ejecución.

    Solo lee: nunca escribe ni llama al registrador. Cada línea debe ser un
    objeto JSON con los cinco campos exactos, valores de texto no vacíos, el
    run_id esperado y una fecha ISO en UTC; además deben aparecer los tres
    eventos de EVENTOS_REQUERIDOS, en cualquier orden.
    """

    def __init__(self, requeridos=None):
        """Recibe los eventos obligatorios; por omisión, EVENTOS_REQUERIDOS.

        Argumentos:
            requeridos: conjunto de tuplas (rol, operacion, resultado).
        """
        self.requeridos = frozenset(requeridos or EVENTOS_REQUERIDOS)

    @staticmethod
    def _sin_claves_repetidas(pares):
        """Construye el objeto JSON y rechaza claves duplicadas."""
        objeto = dict(pares)
        if len(objeto) != len(pares):
            raise ValueError('Clave repetida en el evento')
        return objeto

    @staticmethod
    def _fecha_utc_valida(texto) -> bool:
        """Indica si el texto es una fecha ISO con desplazamiento cero."""
        try:
            fecha = datetime.fromisoformat(texto)
        except ValueError:
            return False
        return fecha.tzinfo is not None and fecha.utcoffset() == timedelta(0)

    def _evento_valido(self, evento, run_id) -> bool:
        """Aplica las reglas de estructura, valores, run_id y fecha."""
        if not isinstance(evento, dict) or set(evento) != set(CAMPOS_EVENTO):
            return False
        if not all(isinstance(v, str) and v.strip() for v in evento.values()):
            return False
        if evento['run_id'] != run_id:
            return False
        return self._fecha_utc_valida(evento['fecha_utc'])

    def verificar(self, ruta, run_id) -> bool:
        """Devuelve True solo si la traza completa cumple todas las reglas.

        Argumentos:
            ruta: archivo JSONL de eventos.
            run_id: identificador que deben compartir todos los eventos.

        Devuelve:
            True si todas las líneas son válidas y están los tres eventos
            requeridos; False en cualquier otro caso, incluidos los errores
            de lectura.
        """
        try:
            texto = Path(ruta).read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            return False
        # Solo el salto de linea separa eventos; splitlines() tambien parte
        # por U+2028, U+2029 y U+0085, que registrar escribe sin escapar.
        lineas = texto.split('\n')
        if lineas[-1] == '':
            lineas.pop()
        if not lineas:
            return False
        vistos = set()
        for linea in lineas:
            try:
                evento = json.loads(
                    linea, object_pairs_hook=self._sin_claves_repetidas)
            except ValueError:
                return False
            if not self._evento_valido(evento, run_id):
                return False
            vistos.add((evento['rol'], evento['operacion'],
                        evento['resultado']))
        return self.requeridos <= vistos


class VerificadorCifrado:
    """Comprueba que el detalle cifra nombre y correo de forma recuperable.

    Compara fila a fila el detalle protegido con el original: el pedido debe
    ser el mismo, cada campo protegido no debe estar en claro y su token debe
    descifrarse exactamente al valor original con la clave cargada.
    """

    def __init__(self, cifrador=None):
        """Recibe el cifrador; si se omite, se carga desde DATAOPS_KEY.

        Argumentos:
            cifrador: instancia de lab1.CifradorCampos.
        """
        self._cifrador = cifrador

    def verificar(self, detalle, entrada) -> bool:
        """Devuelve True si todas las filas protegidas son recuperables.

        Argumentos:
            detalle: CSV con nombre y correo cifrados.
            entrada: CSV original de pedidos.

        Devuelve:
            True si las filas se corresponden y todos los tokens descifran al
            valor original; False si alguna regla no se cumple.

        Lanza:
            ValueError: si falta la clave o algún CSV incumple el contrato.
            cryptography.fernet.InvalidToken: si la clave no corresponde.
        """
        originales = lab1.leer_pedidos(entrada)
        protegidas = lab1.leer_pedidos(detalle)
        if len(originales) != len(protegidas):
            return False
        cifrador = self._cifrador or lab1.CifradorCampos.desde_entorno()
        for original, protegida in zip(originales, protegidas):
            if original['pedido_id'] != protegida['pedido_id']:
                return False
            for campo in lab1.CAMPOS_PROTEGIDOS:
                token = protegida[campo]
                if token == original[campo]:
                    return False
                if cifrador.descifrar(token) != original[campo]:
                    return False
        return True


class ReporteAuditoria:
    """Acumula los controles de una auditoría y la huella verificada.

    Cada control tiene nombre, estado (SATISFACTORIO, FALLIDO o NO_EVALUADO),
    evidencia y acción propuesta. Una comprobación que lanza una excepción
    nunca se da por satisfactoria.
    """

    def __init__(self):
        """Empieza sin controles y sin huella de entrada verificada."""
        self.controles = []
        self.hash_entrada = None

    def agregar(self, control, estado, evidencia, accion=''):
        """Añade un control con su estado, evidencia y acción."""
        self.controles.append({
            'control': control, 'estado': estado,
            'evidencia': evidencia, 'accion': accion,
        })

    def revisar(self, control, comprobacion, evidencia):
        """Ejecuta una comprobación y registra su estado.

        Argumentos:
            control: nombre del control.
            comprobacion: función sin argumentos que devuelve un booleano.
            evidencia: ruta o descripción de la evidencia revisada.
        """
        try:
            correcto = comprobacion() is True
        except NotImplementedError:
            self.agregar(control, NO_EVALUADO, evidencia,
                         'Completar TODO correspondiente')
        except Exception as exc:
            # El fallo de una comprobacion se informa y no detiene la auditoria.
            self.agregar(control, FALLIDO, evidencia,
                         f'Revisar {type(exc).__name__}')
        else:
            self.agregar(control, SATISFACTORIO if correcto else FALLIDO,
                         evidencia, '' if correcto else 'Investigar control')

    def estado(self, control):
        """Devuelve el estado del control o None si no se registró."""
        for registro in self.controles:
            if registro['control'] == control:
                return registro['estado']
        return None

    def completar_no_evaluados(self):
        """Marca NO_EVALUADO los controles previstos que no se ejecutaron."""
        for nombre in CONTROLES_PREVISTOS:
            if self.estado(nombre) is None:
                self.agregar(nombre, NO_EVALUADO, 'Sin ejecucion',
                             'Resolver bloqueo y repetir en nueva carpeta')


class AuditorNova:
    """Ejecuta el pipeline auditado y escribe el reporte de cinco controles.

    El orden es fijo: autorización del rol, evento PERMITIDO, integridad,
    pipeline, evento COMPLETADO, cifrado, minimización, intento simulado de
    un analista (evento DENEGADO) y trazabilidad. Un bloqueo detiene el resto
    y deja los controles pendientes en NO_EVALUADO. Cada auditoría usa una
    carpeta nueva y nunca sobrescribe ejecuciones anteriores.
    """

    def __init__(self, ejecuciones=None, pipeline=None, registrador=None,
                 minimizacion=None, trazabilidad=None, cifrado=None,
                 reloj=None):
        """Inyecta carpeta y colaboradores; cada uno tiene valor por defecto.

        Argumentos:
            ejecuciones: carpeta donde se crean las ejecuciones.
            pipeline: instancia de lab1.PipelineNova.
            registrador: instancia de RegistradorEventos.
            minimizacion: instancia de VerificadorMinimizacion.
            trazabilidad: instancia de VerificadorTrazabilidad.
            cifrado: instancia de VerificadorCifrado.
            reloj: función que devuelve la hora UTC de eventos y reporte.
        """
        self.ejecuciones = Path(ejecuciones or EJECUCIONES)
        self.pipeline = pipeline or lab1.PipelineNova()
        self.registrador = registrador or RegistradorEventos(reloj)
        self.minimizacion = minimizacion or VerificadorMinimizacion()
        self.trazabilidad = trazabilidad or VerificadorTrazabilidad()
        self.cifrado = cifrado or VerificadorCifrado()
        self.reloj = reloj or ahora_utc

    def _aplicar_controles(self, reporte, rol, entrada, referencia, carpeta,
                           run_id):
        """Aplica los controles en orden y los anota en el reporte.

        La huella se guarda en cuanto la integridad se verifica, de modo que
        el reporte la conserva aunque un paso posterior falle.

        Lanza:
            PermissionError: si el rol no puede ejecutar.
            ValueError: si falla la integridad o falta la clave.
            OSError: si falta un archivo o el destino ya existe.
        """
        eventos = carpeta / 'eventos.jsonl'
        control_acceso = self.pipeline.control_acceso
        try:
            control_acceso.autorizar(rol, 'ejecutar')
        except PermissionError:
            try:
                self.registrador.registrar(eventos, run_id, rol, 'ejecutar',
                                           'DENEGADO')
                evidencia = 'eventos.jsonl'
            except ValueError:
                # Un rol vacio no se puede registrar: el reporte lo dice en
                # vez de citar un evento que no existe.
                evidencia = 'Rol vacio; denegacion sin evento'
            reporte.agregar('AUTORIZACION_INICIAL', FALLIDO, evidencia,
                            'Usar operador')
            raise
        self.registrador.registrar(eventos, run_id, rol, 'ejecutar',
                                   'PERMITIDO')
        # No se escribe ninguna salida si la entrada no coincide.
        try:
            huella = self.pipeline.verificador.verificar(entrada, referencia)
        except ValueError:
            reporte.agregar('INTEGRIDAD', FALLIDO,
                            'Comparacion con referencia confiable',
                            'Revisar origen del archivo; no procesar')
            raise
        reporte.hash_entrada = huella
        reporte.agregar('INTEGRIDAD', SATISFACTORIO, 'hash_entrada del reporte')
        resultado = self.pipeline.ejecutar(rol, entrada, referencia,
                                           carpeta / 'salidas')
        self.registrador.registrar(eventos, run_id, rol, 'pipeline',
                                   'COMPLETADO')
        reporte.revisar('CIFRADO', lambda: self.cifrado.verificar(
            resultado['detalle'], entrada), 'salidas/detalle_protegido.csv')
        reporte.revisar('MINIMIZACION', lambda: self.minimizacion.verificar(
            resultado['resumen']), 'salidas/resumen.csv')
        # Intento simulado por el orquestador; no es una persona autenticada.
        try:
            control_acceso.autorizar('analista', 'ejecutar')
        except PermissionError:
            self.registrador.registrar(eventos, run_id, 'analista',
                                       'ejecutar', 'DENEGADO')
            reporte.agregar('ACCESO_DENEGADO', SATISFACTORIO, 'eventos.jsonl')
        else:
            reporte.agregar('ACCESO_DENEGADO', FALLIDO,
                            'No se produjo PermissionError',
                            'Corregir autorizar antes de continuar')
        reporte.revisar('TRAZABILIDAD', lambda: self.trazabilidad.verificar(
            eventos, run_id), 'eventos.jsonl')

    def auditar(self, rol, entrada, referencia) -> Path:
        """Audita una ejecución completa y escribe su reporte.

        Argumentos:
            rol: rol que solicita la ejecución.
            entrada: CSV original de pedidos.
            referencia: archivo con la huella confiable de la entrada.

        Devuelve:
            Ruta de reporte.json dentro de la carpeta nueva de la ejecución.

        Lanza:
            FileExistsError: si la carpeta del run_id ya existe.
        """
        run_id = uuid.uuid4().hex
        carpeta = self.ejecuciones / run_id
        carpeta.mkdir(parents=True, exist_ok=False)
        reporte = ReporteAuditoria()
        try:
            self._aplicar_controles(reporte, rol, entrada, referencia,
                                    carpeta, run_id)
        except NotImplementedError:
            reporte.agregar('EJECUCION', NO_EVALUADO, 'Codigo base',
                            'Completar TODO 1 a 5 antes de continuar')
        except Exception as exc:
            # Cualquier bloqueo queda en el reporte junto con su evidencia.
            reporte.agregar('EJECUCION', FALLIDO, type(exc).__name__,
                            'Revisar permisos, integridad y entorno')
        reporte.completar_no_evaluados()
        integridad = reporte.estado('INTEGRIDAD') == SATISFACTORIO
        contenido = {
            'run_id': run_id,
            'fecha_utc': self.reloj().isoformat(),
            'rol_ejecutor': rol,
            'hash_entrada': reporte.hash_entrada if integridad else None,
            'controles': reporte.controles,
        }
        ruta = carpeta / 'reporte.json'
        ruta.write_text(json.dumps(contenido, indent=2, ensure_ascii=False),
                        encoding='utf-8')
        # Ruta e identificador; nunca contenido personal o claves.
        print(f'Reporte generado: {ruta}')
        return ruta

    def consultar(self, rol, reporte) -> str:
        """Devuelve el texto de un reporte si el rol puede ver evidencias.

        Argumentos:
            rol: rol que solicita la consulta.
            reporte: ruta de reporte.json.

        Devuelve:
            Contenido del reporte.

        Lanza:
            PermissionError: si el rol no tiene la operación evidencias.
            ValueError: si la ruta no es ejecuciones/RUN_ID/reporte.json; así
                --reporte no sirve para leer la clave ni los datos originales.
            OSError: si el reporte no puede leerse.
        """
        self.pipeline.control_acceso.autorizar(rol, 'evidencias')
        ruta = Path(reporte).resolve()
        if (ruta.name != 'reporte.json'
                or ruta.parent.parent != self.ejecuciones.resolve()):
            raise ValueError(
                'Solo se consultan reportes ejecuciones/RUN_ID/reporte.json')
        return ruta.read_text(encoding='utf-8')


class InterfazAuditoria:
    """Interfaz de línea de comandos de la auditoría.

    ejecutar termina con código 0 aunque el reporte contenga fallos: los
    estados se interpretan en el JSON. consultar comprueba el permiso antes
    de exigir --reporte; una denegación termina con código 1, nombra la
    excepción PermissionError y no muestra el reporte. Solo se leen rutas
    ejecuciones/RUN_ID/reporte.json.
    """

    def __init__(self, auditor=None):
        """Recibe el auditor a usar; por omisión crea uno nuevo.

        Argumentos:
            auditor: instancia de AuditorNova.
        """
        self.auditor = auditor or AuditorNova()

    @staticmethod
    def construir_parser():
        """Construye el analizador de argumentos con sus valores por defecto.

        Devuelve:
            Instancia de argparse.ArgumentParser.
        """
        parser = argparse.ArgumentParser(
            description='Auditoria del pipeline de Comercial Nova')
        parser.add_argument('accion', choices=['ejecutar', 'consultar'])
        parser.add_argument('--rol', default='operador')
        parser.add_argument('--entrada', type=Path,
                            default=lab1.DATOS / 'pedidos.csv')
        parser.add_argument('--referencia', type=Path,
                            default=BASE / 'referencia.sha256')
        parser.add_argument('--reporte', type=Path)
        return parser

    def ejecutar(self, argv=None):
        """Interpreta los argumentos y realiza la acción solicitada.

        Argumentos:
            argv: lista de argumentos; por omisión se usa sys.argv.
        """
        parser = self.construir_parser()
        args = parser.parse_args(argv)
        if args.accion == 'ejecutar':
            self.auditor.auditar(args.rol, args.entrada, args.referencia)
            return
        try:
            self.auditor.pipeline.control_acceso.autorizar(
                args.rol, 'evidencias')
            if not args.reporte:
                parser.error('consultar requiere --reporte RUTA')
            texto = self.auditor.consultar(args.rol, args.reporte)
        except (PermissionError, ValueError, OSError) as exc:
            parser.exit(1, f'BLOQUEADO: {type(exc).__name__}: {exc}\n')
        print(texto)


def registrar_evento(ruta, run_id, rol, operacion, resultado):
    """Anexa un evento JSON por línea en UTF-8 (TODO 5)."""
    RegistradorEventos().registrar(ruta, run_id, rol, operacion, resultado)


def comprobar_minimizacion(ruta):
    """Devuelve True solo si el resumen cumple el esquema mínimo (TODO 6)."""
    return VerificadorMinimizacion().verificar(ruta)


def comprobar_trazabilidad(ruta, run_id):
    """Devuelve True solo si la traza de la ejecución es válida (TODO 7)."""
    return VerificadorTrazabilidad().verificar(ruta, run_id)


def comprobar_cifrado(detalle, entrada):
    """Comprueba que el detalle cifra y recupera nombre y correo."""
    return VerificadorCifrado().verificar(detalle, entrada)


def auditar(rol, entrada, referencia):
    """Audita una ejecución en ejecuciones/RUN_ID y devuelve el reporte."""
    return AuditorNova(EJECUCIONES).auditar(rol, entrada, referencia)


def main():
    """Punto de entrada de la línea de comandos."""
    InterfazAuditoria().ejecutar()


if __name__ == '__main__':
    main()
