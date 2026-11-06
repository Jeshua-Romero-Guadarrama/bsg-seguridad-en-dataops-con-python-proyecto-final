"""Pruebas de PipelineNova: caso autorizado, bloqueos y orden de controles."""
import csv
from decimal import Decimal

import pytest
from cryptography.fernet import Fernet, InvalidToken

import lab1
from lab1 import CAMPOS, PipelineNova

RESUMEN_ESPERADO = [
    ('Merida', '4000.00'),
    ('Puebla', '2500.00'),
    ('Villahermosa', '4250.00'),
]
MUESTRA_ESPERADA = {
    'nombre_cliente': 'Cliente Prueba 001',
    'correo': 'cliente001@example.com',
}


def leer_csv(ruta):
    """Devuelve el encabezado y las filas de un CSV como diccionarios."""
    with ruta.open(encoding='utf-8', newline='') as f:
        lector = csv.DictReader(f)
        return lector.fieldnames, list(lector)


@pytest.fixture
def ejecucion(entorno):
    """Ejecuta el pipeline como operador sobre un destino nuevo."""
    destino = entorno.salidas / 'lab1'
    resultado = PipelineNova().ejecutar(
        'operador', entorno.entrada, entorno.referencia, destino)
    return entorno, destino, resultado


class PruebaEjecucionAutorizada:
    """Caso autorizado: operador ejecuta y genera salidas correctas."""

    def prueba_devuelve_doce_filas(self, ejecucion):
        """ejecutar devuelve filas == 12 y las rutas de salida."""
        entorno, destino, resultado = ejecucion
        assert resultado['filas'] == 12
        assert resultado['detalle'] == destino / 'detalle_protegido.csv'
        assert resultado['resumen'] == destino / 'resumen.csv'
        assert resultado['hash_entrada'] == (
            entorno.referencia.read_text().strip())

    def prueba_detalle_cifrado(self, ejecucion):
        """Nombre y correo son tokens Fernet; el resto queda igual."""
        entorno, destino, _ = ejecucion
        _, originales = leer_csv(entorno.entrada)
        campos, protegidas = leer_csv(destino / 'detalle_protegido.csv')
        assert campos == CAMPOS
        assert len(protegidas) == 12
        for original, protegida in zip(originales, protegidas):
            for campo in ('nombre_cliente', 'correo'):
                token = protegida[campo]
                assert token.startswith('gAAAA')
                assert '@' not in token
                assert 'Cliente Prueba' not in token
            for campo in CAMPOS:
                if campo not in ('nombre_cliente', 'correo'):
                    assert protegida[campo] == original[campo]

    def prueba_resumen_por_ciudad(self, ejecucion):
        """El resumen tiene tres ciudades en orden y total 10750.00."""
        _, destino, _ = ejecucion
        campos, filas = leer_csv(destino / 'resumen.csv')
        assert campos == ['ciudad', 'total_ventas']
        assert [(f['ciudad'], f['total_ventas']) for f in filas] == (
            RESUMEN_ESPERADO)
        total = sum(Decimal(f['total_ventas']) for f in filas)
        assert f'{total:.2f}' == '10750.00'

    def prueba_cancelados_no_suman(self, ejecucion):
        """Los tres pedidos cancelados quedan fuera de los totales."""
        entorno, destino, _ = ejecucion
        _, originales = leer_csv(entorno.entrada)
        cancelados = [f for f in originales if f['estado'] == 'Cancelado']
        assert len(cancelados) == 3
        todos = sum(Decimal(f['importe']) for f in originales)
        excluido = sum(Decimal(f['importe']) for f in cancelados)
        _, filas = leer_csv(destino / 'resumen.csv')
        total = sum(Decimal(f['total_ventas']) for f in filas)
        assert total == todos - excluido == Decimal('10750.00')


class PruebaConsultasPosteriores:
    """Resumen y recuperación solo para los roles asignados."""

    def prueba_resumen_como_analista(self, ejecucion):
        """El analista obtiene el texto del resumen."""
        _, destino, _ = ejecucion
        texto = PipelineNova().consultar_resumen('analista', destino)
        assert texto.splitlines() == [
            'ciudad,total_ventas',
            'Merida,4000.00',
            'Puebla,2500.00',
            'Villahermosa,4250.00',
        ]

    @pytest.mark.parametrize('rol', ['operador', 'auditor'])
    def prueba_resumen_denegado(self, ejecucion, rol):
        """Operador y auditor no consultan el resumen."""
        _, destino, _ = ejecucion
        with pytest.raises(PermissionError):
            PipelineNova().consultar_resumen(rol, destino)

    def prueba_recuperar_como_operador(self, ejecucion):
        """El operador recupera la primera muestra ficticia."""
        _, destino, _ = ejecucion
        assert PipelineNova().recuperar_muestra('operador', destino) == (
            MUESTRA_ESPERADA)
        assert lab1.recuperar_muestra('operador', destino) == (
            MUESTRA_ESPERADA)

    @pytest.mark.parametrize('rol', ['analista', 'auditor'])
    def prueba_recuperar_denegado(self, ejecucion, rol):
        """Analista y auditor no recuperan datos personales."""
        _, destino, _ = ejecucion
        with pytest.raises(PermissionError):
            PipelineNova().recuperar_muestra(rol, destino)

    def prueba_recuperar_con_otra_clave(self, ejecucion, monkeypatch):
        """Una clave distinta no descifra las salidas: InvalidToken."""
        _, destino, _ = ejecucion
        monkeypatch.setenv('DATAOPS_KEY', Fernet.generate_key().decode())
        with pytest.raises(InvalidToken):
            PipelineNova().recuperar_muestra('operador', destino)


class PruebaBloqueosSinEscritura:
    """Un bloqueo nunca crea el destino ni sobrescribe salidas previas."""

    @pytest.mark.parametrize('rol', ['analista', 'auditor', 'desconocido'])
    def prueba_rol_sin_permiso(self, entorno, rol):
        """Ejecutar sin permiso lanza PermissionError y no crea destino."""
        destino = entorno.salidas / f'denegada_{rol}'
        with pytest.raises(PermissionError):
            PipelineNova().ejecutar(
                rol, entorno.entrada, entorno.referencia, destino)
        assert not destino.exists()

    def prueba_entrada_alterada(self, entorno):
        """Una entrada alterada bloquea por integridad sin crear destino."""
        alterada = entorno.alterar_entrada()
        destino = entorno.salidas / 'alterada'
        with pytest.raises(ValueError, match='Integridad de entrada no valida'):
            PipelineNova().ejecutar(
                'operador', alterada, entorno.referencia, destino)
        assert not destino.exists()

    def prueba_falta_clave(self, entorno, monkeypatch):
        """Sin DATAOPS_KEY el pipeline se detiene antes de crear destino."""
        monkeypatch.delenv('DATAOPS_KEY')
        destino = entorno.salidas / 'sin_clave'
        with pytest.raises(ValueError, match='Falta DATAOPS_KEY'):
            PipelineNova().ejecutar(
                'operador', entorno.entrada, entorno.referencia, destino)
        assert not destino.exists()

    def prueba_fila_con_columnas_de_mas(self, entorno):
        """Una fila de ocho campos se rechaza sin crear el destino."""
        lineas = entorno.entrada.read_text(encoding='utf-8').splitlines()
        sobrante = entorno.entrada.parent / 'columnas_de_mas.csv'
        sobrante.write_text(f'{lineas[0]}\n{lineas[1]},extra\n',
                            encoding='utf-8')
        referencia = entorno.base / 'columnas_de_mas.sha256'
        referencia.write_text(lab1.calcular_hash(sobrante), encoding='ascii')
        destino = entorno.salidas / 'columnas_de_mas'
        with pytest.raises(ValueError, match='Fila incompleta'):
            PipelineNova().ejecutar(
                'operador', sobrante, referencia, destino)
        assert not destino.exists()

    def prueba_destino_existente_no_se_sobrescribe(self, ejecucion):
        """Un destino existente lanza FileExistsError y conserva los bytes."""
        entorno, destino, _ = ejecucion
        antes = {p.name: p.read_bytes() for p in destino.iterdir()}
        with pytest.raises(FileExistsError) as error:
            PipelineNova().ejecutar(
                'operador', entorno.entrada, entorno.referencia, destino)
        assert isinstance(error.value, OSError)
        despues = {p.name: p.read_bytes() for p in destino.iterdir()}
        assert despues == antes


class PruebaOrdenDeControles:
    """El permiso se comprueba antes que la integridad y esta antes que el contrato."""

    def prueba_permiso_antes_que_integridad(self, entorno):
        """Rol sin permiso y entrada alterada: gana PermissionError."""
        alterada = entorno.alterar_entrada()
        destino = entorno.salidas / 'doble_fallo'
        with pytest.raises(PermissionError):
            PipelineNova().ejecutar(
                'analista', alterada, entorno.referencia, destino)
        assert not destino.exists()

    def prueba_integridad_antes_que_contrato(self, entorno):
        """Rol permitido y entrada que rompe el contrato: gana la integridad."""
        rota = entorno.entrada.parent / 'contrato_roto.csv'
        rota.write_text('columna_ajena\nvalor\n', encoding='utf-8')
        destino = entorno.salidas / 'contrato_roto'
        with pytest.raises(ValueError) as error:
            PipelineNova().ejecutar(
                'operador', rota, entorno.referencia, destino)
        assert str(error.value) == 'Integridad de entrada no valida'
        assert not destino.exists()

    def prueba_entrada_alterada_da_error_de_integridad(self, entorno):
        """La copia alterada es válida por contrato, pero falla integridad."""
        alterada = entorno.alterar_entrada()
        assert len(lab1.leer_pedidos(alterada)) == 12
        with pytest.raises(ValueError) as error:
            PipelineNova().ejecutar('operador', alterada, entorno.referencia,
                                    entorno.salidas / 'alterada')
        assert str(error.value) == 'Integridad de entrada no valida'


class PruebaRepeticion:
    """Repetir con un destino nuevo funciona sin tocar el anterior."""

    def prueba_segunda_ejecucion_en_destino_nuevo(self, ejecucion):
        """Las tres operaciones permitidas funcionan sobre el destino nuevo."""
        entorno, destino, _ = ejecucion
        antes = (destino / 'resumen.csv').read_bytes()
        repeticion = entorno.salidas / 'lab1_repeticion'
        pipeline = PipelineNova()
        resultado = pipeline.ejecutar(
            'operador', entorno.entrada, entorno.referencia, repeticion)
        assert resultado['filas'] == 12
        assert 'Villahermosa,4250.00' in pipeline.consultar_resumen(
            'analista', repeticion)
        assert pipeline.recuperar_muestra('operador', repeticion) == (
            MUESTRA_ESPERADA)
        assert (destino / 'resumen.csv').read_bytes() == antes
