"""Comprobaciones de 1A por etapas (paquete 2.1); sin soluciones de los TODO.

Verifica con las funciones de lab1.py que el original coincide con la
referencia confiable y que una copia con un solo importe alterado deja de
coincidir (TODO 1), que el cifrado produce un token Fernet ASCII válido
(TODO 3) y que el descifrado recupera el texto original (TODO 4). La etapa 1
crea datos/pedidos_prueba_parte1.csv si falta y nunca la sobrescribe.

Uso:
    python comprobar_1a.py [--todo {1,3,4}] [--base CARPETA]

Sin --todo prueba 1, 3 y 4 en orden. Sin --base se usa la carpeta del
repositorio (comportamiento original). Con --base se usan CARPETA/datos y
CARPETA/referencia.sha256, lo que permite comprobar un entorno temporal
creado con PreparadorEntorno.

Códigos de salida: 0 si las etapas pasan, 1 si hay que revisar algo y 2 si un
TODO sigue pendiente o los argumentos no son válidos.
"""
import argparse
import hashlib
import sys
from pathlib import Path

VALORES_PRUEBA = ('cliente001@example.com', 'Cliente Prueba Ñ')


class Pendiente(Exception):
    """Un TODO de lab1.py sigue sin implementar."""


class Revisar(Exception):
    """Una comprobación no dio el resultado esperado."""


def exigir(condicion, mensaje):
    """Lanza Revisar con el mensaje si la condición no se cumple."""
    if not condicion:
        raise Revisar(mensaje)


class ComprobadorLaboratorio1A:
    """Ejecuta las etapas del tramo 1A sobre una carpeta base."""

    def __init__(self, lab1, base=None):
        """Define las rutas de datos y referencia.

        Argumentos:
            lab1: módulo lab1 ya importado.
            base: carpeta del entorno; por omisión, la del módulo lab1.
        """
        self.lab1 = lab1
        self.base = lab1.BASE if base is None else Path(base)
        self.datos = lab1.DATOS if base is None else self.base / 'datos'

    def probar_hash(self):
        """TODO 1 no usa la clave ni llama a cifrar o descifrar."""
        entrada = self.datos / 'pedidos.csv'
        referencia = (self.base / 'referencia.sha256').read_text(
            encoding='ascii').strip()
        contenido = entrada.read_bytes()
        exigir(hashlib.sha256(contenido).hexdigest() == referencia,
               'El original no coincide con la referencia; revisa su origen '
               'sin recalcularla')
        try:
            huella = self.lab1.calcular_hash(entrada)
        except NotImplementedError:
            raise Pendiente('TODO 1: implementa calcular_hash en lab1.py') from None
        exigir(isinstance(huella, str) and len(huella) == 64,
               'TODO 1 debe devolver un str hexadecimal de 64 caracteres, '
               'no imprimirlo')
        exigir(huella == referencia, 'TODO 1: la huella del original no coincide')

        # Prepara la copia de prueba de 1B sin reemplazar una existente.
        alterado = contenido.replace(b'1850.00', b'1851.00', 1)
        exigir(alterado != contenido,
               'No se encontro el importe de prueba en el original')
        copia = self.datos / 'pedidos_prueba_parte1.csv'
        if copia.exists():
            exigir(copia.read_bytes() == alterado,
                   'La copia de prueba existente tiene otro contenido; '
                   'revisala sin sobrescribirla')
        else:
            with copia.open('xb') as archivo:
                archivo.write(alterado)
        try:
            huella_copia = self.lab1.calcular_hash(copia)
        except NotImplementedError:
            raise Pendiente('TODO 1: completa calcular_hash para cualquier '
                            'ruta de archivo') from None
        exigir(huella_copia == hashlib.sha256(alterado).hexdigest(),
               'TODO 1: calcula la huella de la ruta recibida; no devuelvas '
               'un valor fijo')
        exigir(huella_copia != referencia,
               'TODO 1: la modificacion no fue detectada')
        print('TODO 1 OK: original coincide True; copia alterada coincide False.')

    def probar_cifrado(self):
        """TODO 3 se contrasta con Fernet directamente, sin llamar a TODO 4."""
        fernet = self.lab1.cargar_cifrador()
        for valor in VALORES_PRUEBA:
            try:
                token = self.lab1.cifrar(valor, fernet)
            except NotImplementedError:
                raise Pendiente('TODO 3: implementa cifrar en lab1.py') from None
            exigir(isinstance(token, str),
                   'TODO 3 debe devolver un token str, no bytes')
            exigir(token != valor, 'TODO 3: el dato sigue legible')
            try:
                recuperado = fernet.decrypt(token.encode('ascii')).decode('utf-8')
            except Exception:
                raise Revisar('TODO 3: el resultado no es un token Fernet ASCII '
                              'valido para esta clave') from None
            exigir(recuperado == valor,
                   'TODO 3: el token no conserva el texto original')
        print('TODO 3 OK: token ASCII valido y cifrado verificado sin TODO 4.')

    def probar_descifrado(self):
        """TODO 4 usa el TODO 3 ya verificado para producir el token."""
        fernet = self.lab1.cargar_cifrador()
        for valor in VALORES_PRUEBA:
            try:
                token = self.lab1.cifrar(valor, fernet)
            except NotImplementedError:
                raise Pendiente('TODO 4 requiere TODO 3: completa cifrar y '
                                'verifica --todo 3 primero') from None
            exigir(isinstance(token, str),
                   'Antes de TODO 4, verifica cifrar con --todo 3')
            try:
                legible = fernet.decrypt(token.encode('ascii')).decode('utf-8')
            except Exception:
                raise Revisar('Antes de TODO 4, corrige cifrar con --todo 3') from None
            exigir(legible == valor, 'Antes de TODO 4, corrige cifrar con --todo 3')
            try:
                recuperado = self.lab1.descifrar(token, fernet)
            except NotImplementedError:
                raise Pendiente('TODO 4: implementa descifrar en lab1.py') from None
            exigir(isinstance(recuperado, str) and recuperado == valor,
                   'TODO 4 debe devolver el texto UTF-8 original, no bytes ni None')
        print('TODO 4 OK: recuperacion coincidente True.')

    def comprobar(self, todo=None):
        """Ejecuta la etapa indicada o las tres en orden.

        Argumentos:
            todo: 1, 3 o 4; None ejecuta 1, 3 y 4.

        Lanza:
            Pendiente: si algún TODO de lab1.py sigue pendiente.
            Revisar: si alguna comprobación no da el valor esperado.
            ValueError: si falta DATAOPS_KEY en las etapas 3 y 4.
            OSError: si faltan la entrada o la referencia.
        """
        etapas = {1: self.probar_hash, 3: self.probar_cifrado,
                  4: self.probar_descifrado}
        for numero in ([todo] if todo is not None else [1, 3, 4]):
            etapas[numero]()
        if todo is None:
            print('Repaso de proteccion verificado: TODO 1, 3 y 4 resueltos. '
                  'La preparacion revisa tambien TODO 2.')
        else:
            print(f'Etapa TODO {todo} verificada; este resultado no valida '
                  'las otras etapas.')


def main(argv=None):
    """Interpreta --todo y --base, ejecuta el comprobador y devuelve el código.

    Argumentos:
        argv: lista de argumentos; por omisión se usa sys.argv.

    Devuelve:
        0 si las etapas pasan, 1 si hay que revisar y 2 si falta un TODO.
    """
    parser = argparse.ArgumentParser(
        description='Valida TODO 1, 3 o 4 por separado; sin --todo prueba 1, '
                    '3 y 4 en orden.')
    parser.add_argument('--todo', type=int, choices=[1, 3, 4],
                        help='Etapa que quieres comprobar; TODO 4 requiere TODO 3')
    parser.add_argument('--base', type=Path, default=None,
                        help='carpeta base con datos/ y referencia.sha256')
    args = parser.parse_args(argv)
    try:
        import lab1
        exigir(Path(lab1.__file__).resolve().parent
               == Path(__file__).resolve().parent,
               'Coloca este comprobador junto a lab1.py en comercial_nova')
        ComprobadorLaboratorio1A(lab1, args.base).comprobar(args.todo)
        return 0
    except Pendiente as exc:
        print(f'PENDIENTE: {exc}', file=sys.stderr)
        return 2
    except Revisar as exc:
        print(f'REVISAR: {exc}', file=sys.stderr)
        return 1
    except ModuleNotFoundError:
        print('REVISAR: faltan lab1.py o las dependencias; revisa '
              'GUIA_PARTICIPANTE.md', file=sys.stderr)
        return 1
    except FileNotFoundError:
        print('REVISAR: falta un archivo de preparacion; revisa '
              'GUIA_PARTICIPANTE.md', file=sys.stderr)
        return 1
    except ValueError:
        print('REVISAR: comprueba DATAOPS_KEY y los tipos o valores devueltos; '
              'consulta REPASO_LAB1.md', file=sys.stderr)
        return 1
    except Exception as exc:
        # Solo el tipo de la excepcion: su texto podria contener datos.
        print(f'REVISAR: {type(exc).__name__}; consulta REPASO_LAB1.md y '
              'revisa la etapa seleccionada', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
