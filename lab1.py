"""Base resuelta del Laboratorio 1 de Comercial Nova (paquete 2.1).

Integra cuatro controles sobre un dataset ficticio de pedidos: autorización
por rol, verificación de integridad con SHA-256 frente a una referencia
confiable, validación del contrato de datos y cifrado Fernet de los campos
personales. Los TODO 1 a 4 (calcular_hash, autorizar, cifrar y descifrar)
están resueltos. Las funciones de módulo conservan los nombres, parámetros y
contratos del material del curso, delegan en las clases y son las que
reutiliza lab2.py.

Uso:
    python lab1.py {inspeccionar,ejecutar,resumen,recuperar} [--rol ROL]
        [--entrada RUTA] [--referencia RUTA] [--destino RUTA]
"""
import argparse
import csv
import hashlib
import json
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

from cryptography.fernet import Fernet

BASE = Path(__file__).resolve().parent
DATOS = BASE / 'datos'
SALIDAS = BASE / 'salidas'
PERMISOS = {
    'operador': {'ejecutar', 'recuperar'},
    'analista': {'resumen'},
    'auditor': {'evidencias'},
}
CAMPOS = [
    'pedido_id', 'cliente_id', 'nombre_cliente',
    'correo', 'ciudad', 'importe', 'estado',
]
CAMPOS_PROTEGIDOS = ('nombre_cliente', 'correo')
CAMPOS_RESUMEN = ['ciudad', 'total_ventas']
ESTADOS_VALIDOS = {'Confirmado', 'Cancelado'}


class CalculadoraHuella:
    """Calcula la huella SHA-256 de un archivo.

    Lee el archivo por bloques para que el consumo de memoria no dependa de su
    tamaño: los mismos bytes en el mismo orden producen la misma huella.
    """

    TAMANO_BLOQUE = 65536

    def calcular(self, ruta) -> str:
        """Devuelve el SHA-256 hexadecimal de los bytes del archivo.

        Argumentos:
            ruta: ruta del archivo a resumir.

        Devuelve:
            Cadena hexadecimal de 64 caracteres.

        Lanza:
            OSError: si el archivo no existe o no puede leerse.
        """
        huella = hashlib.sha256()
        with Path(ruta).open('rb') as f:
            for bloque in iter(lambda: f.read(self.TAMANO_BLOQUE), b''):
                huella.update(bloque)
        return huella.hexdigest()


class CifradorCampos:
    """Cifra y descifra valores de texto con una clave Fernet.

    No genera claves: recibe un objeto Fernet ya construido o lo crea a partir
    de la variable de entorno indicada.
    """

    def __init__(self, fernet):
        """Guarda el objeto Fernet que se usará en todas las operaciones.

        Argumentos:
            fernet: instancia de cryptography.fernet.Fernet.
        """
        self.fernet = fernet

    @classmethod
    def desde_entorno(cls, variable='DATAOPS_KEY'):
        """Construye el cifrador con la clave guardada en el entorno.

        Argumentos:
            variable: nombre de la variable de entorno que contiene la clave.

        Devuelve:
            Instancia de CifradorCampos lista para usar.

        Lanza:
            ValueError: si la variable no existe o está vacía.
        """
        clave = os.environ.get(variable)
        if not clave:
            raise ValueError('Falta DATAOPS_KEY en el entorno')
        return cls(Fernet(clave.encode('ascii')))

    def cifrar(self, valor: str) -> str:
        """Cifra un texto y devuelve el token como texto ASCII.

        Argumentos:
            valor: texto legible que se protegerá.

        Devuelve:
            Token Fernet en ASCII; varía en cada cifrado.
        """
        return self.fernet.encrypt(valor.encode('utf-8')).decode('ascii')

    def descifrar(self, token: str) -> str:
        """Descifra un token ASCII y devuelve el texto UTF-8 original.

        Argumentos:
            token: token Fernet producido con la misma clave.

        Devuelve:
            Texto original.

        Lanza:
            cryptography.fernet.InvalidToken: si la clave no corresponde o el
            token fue modificado.
        """
        return self.fernet.decrypt(token.encode('ascii')).decode('utf-8')


class ControlAcceso:
    """Matriz de permisos por rol y operación.

    Solo concede lo que la matriz lista de forma explícita: un rol desconocido
    o una operación no asignada se deniegan. Los mensajes de error indican rol
    y operación, nunca datos personales.
    """

    def __init__(self, permisos=None):
        """Recibe la matriz de permisos; por omisión usa PERMISOS.

        Argumentos:
            permisos: diccionario rol -> conjunto de operaciones permitidas.
        """
        self.permisos = PERMISOS if permisos is None else permisos

    def autorizar(self, rol, operacion):
        """Comprueba que el rol tenga asignada la operación.

        Argumentos:
            rol: rol declarado por quien invoca la operación.
            operacion: nombre de la operación solicitada.

        Devuelve:
            True si la operación está permitida.

        Lanza:
            PermissionError: si el rol es desconocido o no tiene la operación.
        """
        if rol not in self.permisos:
            raise PermissionError(f'Rol desconocido: {rol!r}')
        if operacion not in self.permisos[rol]:
            raise PermissionError(
                f'Rol {rol!r} sin permiso para {operacion!r}')
        return True


class ValidadorPedidos:
    """Lee un CSV de pedidos y valida su contrato de datos.

    Comprueba columnas y orden, dataset no vacío, identificadores únicos,
    importes decimales finitos y no negativos y estados permitidos.
    """

    def leer(self, ruta) -> list:
        """Lee y valida los pedidos del archivo indicado.

        Argumentos:
            ruta: ruta del CSV con las columnas de CAMPOS.

        Devuelve:
            Lista de diccionarios, uno por fila de datos.

        Lanza:
            ValueError: si el archivo incumple cualquier regla del contrato.
            OSError: si el archivo no puede abrirse.
        """
        with Path(ruta).open(encoding='utf-8', newline='') as f:
            lector = csv.DictReader(f)
            if lector.fieldnames != CAMPOS:
                raise ValueError('Columnas distintas del contrato')
            filas = list(lector)
        if not filas:
            raise ValueError('Dataset vacio')
        # DictReader guarda las columnas sobrantes bajo la clave None y
        # rellena con None las que faltan.
        for fila in filas:
            if None in fila or None in fila.values():
                raise ValueError('Fila incompleta o con columnas de mas')
        ids = [fila['pedido_id'] for fila in filas]
        if len(ids) != len(set(ids)):
            raise ValueError('Identificadores duplicados')
        for fila in filas:
            try:
                monto = Decimal(fila['importe'])
            except (InvalidOperation, TypeError):
                raise ValueError('Importe invalido') from None
            if not monto.is_finite() or monto < 0:
                raise ValueError('Importe invalido')
            if fila['estado'] not in ESTADOS_VALIDOS:
                raise ValueError('Estado invalido')
        return filas


class VerificadorIntegridad:
    """Compara la huella de una entrada con una referencia confiable.

    La referencia representa el alta inicial del original; nunca se recalcula
    para aceptar un archivo sospechoso.
    """

    def __init__(self, calculadora=None):
        """Recibe la calculadora de huellas; por omisión usa SHA-256.

        Argumentos:
            calculadora: objeto con método calcular(ruta) -> str.
        """
        self.calculadora = calculadora or CalculadoraHuella()

    def verificar(self, entrada, referencia) -> str:
        """Verifica que la entrada coincida con la huella de referencia.

        Argumentos:
            entrada: ruta del CSV que se va a procesar.
            referencia: ruta del archivo con la huella confiable.

        Devuelve:
            Huella hexadecimal de la entrada verificada.

        Lanza:
            ValueError: si la huella no coincide con la referencia.
            OSError: si alguno de los archivos no puede leerse.
        """
        esperado = Path(referencia).read_text().strip()
        actual = self.calculadora.calcular(entrada)
        if actual != esperado:
            raise ValueError('Integridad de entrada no valida')
        return actual


class EscritorCsv:
    """Escribe archivos CSV en UTF-8 con encabezado."""

    @staticmethod
    def escribir(ruta, campos, filas):
        """Escribe las filas en la ruta indicada con el orden de campos dado.

        Argumentos:
            ruta: archivo de salida.
            campos: lista ordenada de nombres de columna.
            filas: iterable de diccionarios con esas columnas.
        """
        with Path(ruta).open('w', encoding='utf-8', newline='') as f:
            escritor = csv.DictWriter(f, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(filas)


class PipelineNova:
    """Orquesta los controles y genera las salidas protegidas.

    El orden de ejecutar es obligatorio: permiso, integridad, validación,
    carga del cifrador, cifrado y escritura. El destino solo se crea cuando
    todos los controles anteriores se superaron, de modo que un bloqueo nunca
    deja salidas parciales.
    """

    def __init__(self, control_acceso=None, validador=None,
                 verificador=None, cifrador=None):
        """Inyecta los colaboradores; cada uno tiene un valor por defecto.

        Argumentos:
            control_acceso: instancia de ControlAcceso.
            validador: instancia de ValidadorPedidos.
            verificador: instancia de VerificadorIntegridad.
            cifrador: instancia de CifradorCampos; si se omite, se carga
                desde DATAOPS_KEY en el momento en que se necesita.
        """
        self.control_acceso = control_acceso or ControlAcceso()
        self.validador = validador or ValidadorPedidos()
        self.verificador = verificador or VerificadorIntegridad()
        self._cifrador = cifrador

    def _obtener_cifrador(self):
        """Devuelve el cifrador inyectado o lo carga desde el entorno."""
        return self._cifrador or CifradorCampos.desde_entorno()

    @staticmethod
    def _totales_por_ciudad(filas):
        """Suma los importes confirmados por ciudad, ordenados por ciudad."""
        totales = {}
        for fila in filas:
            if fila['estado'] == 'Confirmado':
                ciudad = fila['ciudad']
                totales[ciudad] = (
                    totales.get(ciudad, Decimal('0'))
                    + Decimal(fila['importe'])
                )
        return [
            {'ciudad': ciudad, 'total_ventas': f'{total:.2f}'}
            for ciudad, total in sorted(totales.items())
        ]

    def ejecutar(self, rol, entrada, referencia, destino) -> dict:
        """Procesa la entrada y escribe el detalle cifrado y el resumen.

        Argumentos:
            rol: rol que solicita la ejecución.
            entrada: CSV original de pedidos.
            referencia: archivo con la huella confiable de la entrada.
            destino: carpeta nueva donde se escribirán las salidas.

        Devuelve:
            Diccionario con hash_entrada, filas, detalle y resumen.

        Lanza:
            PermissionError: si el rol no puede ejecutar.
            ValueError: si falla la integridad, el contrato o falta la clave.
            FileExistsError: si el destino ya existe (no se sobrescribe).
        """
        self.control_acceso.autorizar(rol, 'ejecutar')
        hash_entrada = self.verificador.verificar(entrada, referencia)
        filas = self.validador.leer(entrada)
        cifrador = self._obtener_cifrador()
        protegidas = []
        for fila in filas:
            copia = dict(fila)
            for campo in CAMPOS_PROTEGIDOS:
                copia[campo] = cifrador.cifrar(fila[campo])
            protegidas.append(copia)
        destino = Path(destino)
        destino.mkdir(parents=True, exist_ok=False)
        detalle = destino / 'detalle_protegido.csv'
        resumen = destino / 'resumen.csv'
        EscritorCsv.escribir(detalle, CAMPOS, protegidas)
        EscritorCsv.escribir(resumen, CAMPOS_RESUMEN,
                             self._totales_por_ciudad(filas))
        return {
            'hash_entrada': hash_entrada,
            'filas': len(filas),
            'detalle': detalle,
            'resumen': resumen,
        }

    def consultar_resumen(self, rol, destino) -> str:
        """Devuelve el texto del resumen de ventas de un destino.

        Argumentos:
            rol: rol que solicita la consulta.
            destino: carpeta de una ejecución válida.

        Devuelve:
            Contenido de resumen.csv.

        Lanza:
            PermissionError: si el rol no puede consultar el resumen.
            OSError: si el resumen no existe.
        """
        self.control_acceso.autorizar(rol, 'resumen')
        return (Path(destino) / 'resumen.csv').read_text(encoding='utf-8')

    def recuperar_muestra(self, rol, destino) -> dict:
        """Descifra los campos protegidos de la primera fila del detalle.

        Argumentos:
            rol: rol que solicita la recuperación.
            destino: carpeta de una ejecución válida.

        Devuelve:
            Diccionario con nombre_cliente y correo descifrados.

        Lanza:
            PermissionError: si el rol no puede recuperar.
            ValueError: si falta la clave o el detalle incumple el contrato.
            cryptography.fernet.InvalidToken: si la clave no corresponde.
        """
        self.control_acceso.autorizar(rol, 'recuperar')
        fila = self.validador.leer(
            Path(destino) / 'detalle_protegido.csv')[0]
        cifrador = self._obtener_cifrador()
        return {campo: cifrador.descifrar(fila[campo])
                for campo in CAMPOS_PROTEGIDOS}


class InterfazLinea:
    """Interfaz de línea de comandos del pipeline.

    Traduce las excepciones a códigos de salida: 2 para un TODO pendiente y 1
    para cualquier bloqueo de permisos, integridad, validación o archivos.
    """

    def __init__(self, pipeline=None):
        """Recibe el pipeline a usar; por omisión crea uno nuevo.

        Argumentos:
            pipeline: instancia de PipelineNova.
        """
        self.pipeline = pipeline or PipelineNova()

    @staticmethod
    def construir_parser():
        """Construye el analizador de argumentos con sus valores por defecto.

        Devuelve:
            Instancia de argparse.ArgumentParser.
        """
        parser = argparse.ArgumentParser(
            description='Pipeline protegido de Comercial Nova')
        parser.add_argument('accion', choices=[
            'inspeccionar', 'ejecutar', 'resumen', 'recuperar',
        ])
        parser.add_argument('--rol', default='operador')
        parser.add_argument('--entrada', type=Path,
                            default=DATOS / 'pedidos.csv')
        parser.add_argument('--referencia', type=Path,
                            default=BASE / 'referencia.sha256')
        parser.add_argument('--destino', type=Path,
                            default=SALIDAS / 'lab1')
        return parser

    def ejecutar(self, argv=None):
        """Interpreta los argumentos y realiza la acción solicitada.

        Argumentos:
            argv: lista de argumentos; por omisión se usa sys.argv.
        """
        parser = self.construir_parser()
        args = parser.parse_args(argv)
        try:
            if args.accion == 'inspeccionar':
                # Diagnostico previo con datos ficticios; omite permisos.
                primera = self.pipeline.validador.leer(args.entrada)[0]
                print(json.dumps(primera, ensure_ascii=False, indent=2))
            elif args.accion == 'ejecutar':
                r = self.pipeline.ejecutar(args.rol, args.entrada,
                                           args.referencia, args.destino)
                print(f"Proceso terminado: {r['filas']} filas")
            elif args.accion == 'resumen':
                print(self.pipeline.consultar_resumen(args.rol, args.destino))
            else:
                print(json.dumps(self.pipeline.recuperar_muestra(
                    args.rol, args.destino), ensure_ascii=False))
        except NotImplementedError as exc:
            parser.exit(2, f'PENDIENTE: {exc}\n')
        except (PermissionError, ValueError, OSError) as exc:
            parser.exit(1, f'BLOQUEADO: {exc}\n')


def calcular_hash(ruta):
    """Devuelve el SHA-256 hexadecimal del archivo (TODO 1)."""
    return CalculadoraHuella().calcular(ruta)


def autorizar(rol, operacion):
    """Autoriza la operación según PERMISOS o lanza PermissionError (TODO 2)."""
    return ControlAcceso(PERMISOS).autorizar(rol, operacion)


def cifrar(valor, fernet):
    """Cifra un texto y devuelve el token ASCII (TODO 3)."""
    return CifradorCampos(fernet).cifrar(valor)


def descifrar(token, fernet):
    """Descifra un token ASCII y devuelve el texto original (TODO 4)."""
    return CifradorCampos(fernet).descifrar(token)


def cargar_cifrador():
    """Devuelve el objeto Fernet construido con DATAOPS_KEY."""
    return CifradorCampos.desde_entorno().fernet


def leer_pedidos(ruta):
    """Lee y valida los pedidos con el contrato de CAMPOS."""
    return ValidadorPedidos().leer(ruta)


def verificar_integridad(entrada, referencia):
    """Compara la huella de la entrada con la referencia confiable."""
    return VerificadorIntegridad().verificar(entrada, referencia)


def escribir_csv(ruta, campos, filas):
    """Escribe un CSV UTF-8 con encabezado."""
    EscritorCsv.escribir(ruta, campos, filas)


def ejecutar(rol, entrada, referencia, destino):
    """Ejecuta el pipeline completo con los controles en orden."""
    return PipelineNova().ejecutar(rol, entrada, referencia, destino)


def consultar_resumen(rol, destino):
    """Devuelve el resumen de ventas si el rol tiene permiso."""
    return PipelineNova().consultar_resumen(rol, destino)


def recuperar_muestra(rol, destino):
    """Recupera la primera muestra descifrada si el rol tiene permiso."""
    return PipelineNova().recuperar_muestra(rol, destino)


def main():
    """Punto de entrada de la línea de comandos."""
    InterfazLinea().ejecutar()


if __name__ == '__main__':
    main()
