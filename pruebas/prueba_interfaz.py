"""Pruebas de la línea de comandos de lab1.py y de comprobar_1a.py por subprocess."""
import json

from pruebas.conftest import RAIZ, lanzar

LAB1 = RAIZ / 'lab1.py'
COMPROBAR = RAIZ / 'comprobar_1a.py'
PRIMERA_FILA = {
    'pedido_id': 'PED-1001',
    'cliente_id': 'CLI-001',
    'nombre_cliente': 'Cliente Prueba 001',
    'correo': 'cliente001@example.com',
    'ciudad': 'Villahermosa',
    'importe': '1850.00',
    'estado': 'Confirmado',
}


def lanzar_lab1(entorno, variables, accion, rol, destino, entrada=None):
    """Ejecuta lab1.py con rutas en tmp_path y devuelve el proceso terminado."""
    return lanzar(LAB1, [
        accion, '--rol', rol,
        '--entrada', entrada or entorno.entrada,
        '--referencia', entorno.referencia,
        '--destino', destino,
    ], variables, entorno.base)


class PruebaInterfazPermitida:
    """Las operaciones permitidas terminan con código 0."""

    def prueba_inspeccionar(self, entorno, entorno_proceso):
        """inspeccionar muestra el primer registro ficticio sin pedir permisos."""
        r = lanzar(LAB1, ['inspeccionar', '--rol', 'desconocido',
                          '--entrada', entorno.entrada],
                   entorno_proceso, entorno.base)
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout) == PRIMERA_FILA

    def prueba_secuencia_permitida(self, entorno, entorno_proceso):
        """ejecutar, resumen y recuperar muestran lo esperado."""
        destino = entorno.salidas / 'repaso_lab1'
        r = lanzar_lab1(entorno, entorno_proceso, 'ejecutar', 'operador',
                        destino)
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == 'Proceso terminado: 12 filas'

        r = lanzar_lab1(entorno, entorno_proceso, 'resumen', 'analista',
                        destino)
        assert r.returncode == 0, r.stderr
        assert r.stdout.split() == [
            'ciudad,total_ventas', 'Merida,4000.00',
            'Puebla,2500.00', 'Villahermosa,4250.00',
        ]

        r = lanzar_lab1(entorno, entorno_proceso, 'recuperar', 'operador',
                        destino)
        assert r.returncode == 0, r.stderr
        assert json.loads(r.stdout) == {
            'nombre_cliente': 'Cliente Prueba 001',
            'correo': 'cliente001@example.com',
        }


class PruebaInterfazBloqueos:
    """Los bloqueos terminan con código 1, BLOQUEADO y sin destino."""

    def prueba_ejecutar_como_analista(self, entorno, entorno_proceso):
        """El analista no puede ejecutar."""
        destino = entorno.salidas / 'repaso_denegada'
        r = lanzar_lab1(entorno, entorno_proceso, 'ejecutar', 'analista',
                        destino)
        assert r.returncode == 1
        assert r.stderr.strip() == (
            "BLOQUEADO: Rol 'analista' sin permiso para 'ejecutar'")
        assert not destino.exists()

    def prueba_ejecutar_con_rol_desconocido(self, entorno, entorno_proceso):
        """Un rol desconocido no puede ejecutar."""
        destino = entorno.salidas / 'denegada_desconocido'
        r = lanzar_lab1(entorno, entorno_proceso, 'ejecutar', 'desconocido',
                        destino)
        assert r.returncode == 1
        assert 'BLOQUEADO: Rol desconocido' in r.stderr
        assert not destino.exists()

    def prueba_recuperar_como_auditor(self, entorno, entorno_proceso):
        """El auditor no recupera la muestra y no ve datos personales."""
        destino = entorno.salidas / 'repaso_lab1'
        assert lanzar_lab1(entorno, entorno_proceso, 'ejecutar', 'operador',
                           destino).returncode == 0
        r = lanzar_lab1(entorno, entorno_proceso, 'recuperar', 'auditor',
                        destino)
        assert r.returncode == 1
        assert 'BLOQUEADO' in r.stderr
        assert '@' not in r.stdout + r.stderr

    def prueba_entrada_alterada(self, entorno, entorno_proceso):
        """La copia alterada se bloquea por integridad."""
        alterada = entorno.alterar_entrada()
        destino = entorno.salidas / 'repaso_alterada'
        r = lanzar_lab1(entorno, entorno_proceso, 'ejecutar', 'operador',
                        destino, entrada=alterada)
        assert r.returncode == 1
        assert r.stderr.strip() == 'BLOQUEADO: Integridad de entrada no valida'
        assert not destino.exists()

    def prueba_sin_clave(self, entorno, entorno_proceso):
        """Sin DATAOPS_KEY no se crea el destino."""
        entorno_proceso.pop('DATAOPS_KEY')
        destino = entorno.salidas / 'sin_clave'
        r = lanzar_lab1(entorno, entorno_proceso, 'ejecutar', 'operador',
                        destino)
        assert r.returncode == 1
        assert r.stderr.strip() == 'BLOQUEADO: Falta DATAOPS_KEY en el entorno'
        assert not destino.exists()

    def prueba_destino_existente(self, entorno, entorno_proceso):
        """Repetir sobre el mismo destino se bloquea sin sobrescribir."""
        destino = entorno.salidas / 'repaso_lab1'
        assert lanzar_lab1(entorno, entorno_proceso, 'ejecutar', 'operador',
                           destino).returncode == 0
        antes = (destino / 'detalle_protegido.csv').read_bytes()
        r = lanzar_lab1(entorno, entorno_proceso, 'ejecutar', 'operador',
                        destino)
        assert r.returncode == 1
        assert r.stderr.startswith('BLOQUEADO')
        assert (destino / 'detalle_protegido.csv').read_bytes() == antes


class PruebaComprobador1A:
    """comprobar_1a.py con --base sobre un entorno temporal."""

    def lanzar_comprobador(self, entorno, variables, *argumentos):
        """Ejecuta comprobar_1a.py con --base y los argumentos dados."""
        return lanzar(COMPROBAR, ['--base', entorno.base, *argumentos],
                      variables, entorno.base)

    def prueba_todo_1_sin_clave(self, entorno, entorno_proceso):
        """--todo 1 no necesita la clave y crea la copia alterada."""
        entorno_proceso.pop('DATAOPS_KEY')
        r = self.lanzar_comprobador(entorno, entorno_proceso, '--todo', '1')
        assert r.returncode == 0, r.stderr
        assert r.stdout.splitlines() == [
            'TODO 1 OK: original coincide True; copia alterada coincide False.',
            'Etapa TODO 1 verificada; este resultado no valida las otras '
            'etapas.',
        ]
        copia = entorno.base / 'datos' / 'pedidos_prueba_parte1.csv'
        assert copia.read_bytes() == entorno.entrada.read_bytes().replace(
            b'1850.00', b'1851.00', 1)

    def prueba_todas_las_etapas(self, entorno, entorno_proceso):
        """Sin --todo verifica 1, 3 y 4 y termina con el repaso verificado."""
        r = self.lanzar_comprobador(entorno, entorno_proceso)
        assert r.returncode == 0, r.stderr
        assert r.stdout.splitlines() == [
            'TODO 1 OK: original coincide True; copia alterada coincide False.',
            'TODO 3 OK: token ASCII valido y cifrado verificado sin TODO 4.',
            'TODO 4 OK: recuperacion coincidente True.',
            'Repaso de proteccion verificado: TODO 1, 3 y 4 resueltos. '
            'La preparacion revisa tambien TODO 2.',
        ]

    def prueba_reutiliza_copia_identica(self, entorno, entorno_proceso):
        """Una copia alterada idéntica se reutiliza sin error."""
        entorno.alterar_entrada()
        r = self.lanzar_comprobador(entorno, entorno_proceso, '--todo', '1')
        assert r.returncode == 0, r.stderr

    def prueba_no_sobrescribe_copia_distinta(self, entorno, entorno_proceso):
        """Una copia con otro contenido detiene la etapa sin reemplazarla."""
        copia = entorno.base / 'datos' / 'pedidos_prueba_parte1.csv'
        copia.write_text('contenido ajeno\n', encoding='utf-8')
        r = self.lanzar_comprobador(entorno, entorno_proceso, '--todo', '1')
        assert r.returncode == 1
        assert r.stderr.startswith('REVISAR: La copia de prueba existente')
        assert copia.read_text(encoding='utf-8') == 'contenido ajeno\n'

    def prueba_todo_3_sin_clave(self, entorno, entorno_proceso):
        """Sin clave, la etapa 3 pide revisar DATAOPS_KEY sin mostrarla."""
        entorno_proceso.pop('DATAOPS_KEY')
        r = self.lanzar_comprobador(entorno, entorno_proceso, '--todo', '3')
        assert r.returncode == 1
        assert 'REVISAR: comprueba DATAOPS_KEY' in r.stderr
        assert entorno.clave.read_text(encoding='ascii').strip() not in (
            r.stdout + r.stderr)

    def prueba_todo_invalido(self, entorno, entorno_proceso):
        """Un --todo fuera de 1, 3 y 4 termina con código 2."""
        r = self.lanzar_comprobador(entorno, entorno_proceso, '--todo', '2')
        assert r.returncode == 2
