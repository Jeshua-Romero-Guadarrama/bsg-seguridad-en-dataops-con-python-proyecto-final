"""Pruebas de la matriz de roles de ControlAcceso (TODO 2)."""
import pytest

import lab1
from lab1 import ControlAcceso

OPERACIONES = ['ejecutar', 'resumen', 'recuperar', 'evidencias']
ESPERADO = {
    ('operador', 'ejecutar'): True,
    ('operador', 'resumen'): False,
    ('operador', 'recuperar'): True,
    ('operador', 'evidencias'): False,
    ('analista', 'ejecutar'): False,
    ('analista', 'resumen'): True,
    ('analista', 'recuperar'): False,
    ('analista', 'evidencias'): False,
    ('auditor', 'ejecutar'): False,
    ('auditor', 'resumen'): False,
    ('auditor', 'recuperar'): False,
    ('auditor', 'evidencias'): True,
}


class PruebaControlAcceso:
    """Comprueba las 12 combinaciones y la denegación por defecto."""

    def prueba_permisos_del_modulo_sin_cambios(self):
        """lab1.PERMISOS conserva el diccionario del material."""
        assert lab1.PERMISOS == {
            'operador': {'ejecutar', 'recuperar'},
            'analista': {'resumen'},
            'auditor': {'evidencias'},
        }

    @pytest.mark.parametrize(('rol', 'operacion'), sorted(ESPERADO))
    def prueba_matriz_completa(self, rol, operacion):
        """Cada combinación rol x operación da el resultado de la matriz."""
        control = ControlAcceso()
        if ESPERADO[(rol, operacion)]:
            assert control.autorizar(rol, operacion) is True
            assert lab1.autorizar(rol, operacion) is True
        else:
            with pytest.raises(PermissionError):
                control.autorizar(rol, operacion)
            with pytest.raises(PermissionError):
                lab1.autorizar(rol, operacion)

    def prueba_rol_desconocido_denegado(self):
        """Un rol fuera de la matriz no recibe ningún permiso."""
        for operacion in OPERACIONES:
            with pytest.raises(PermissionError, match='Rol desconocido'):
                ControlAcceso().autorizar('desconocido', operacion)

    def prueba_operacion_desconocida_denegada(self):
        """Una operación no listada se deniega incluso al operador."""
        for rol in ('operador', 'analista', 'auditor'):
            with pytest.raises(PermissionError):
                ControlAcceso().autorizar(rol, 'borrar')

    @pytest.mark.parametrize(('rol', 'operacion'), [
        ('analista', 'ejecutar'),
        ('auditor', 'recuperar'),
        ('desconocido', 'ejecutar'),
        ('operador', 'borrar'),
    ])
    def prueba_mensaje_sin_datos_personales(self, rol, operacion):
        """El mensaje de denegación no contiene correos ni nombres."""
        with pytest.raises(PermissionError) as error:
            ControlAcceso().autorizar(rol, operacion)
        mensaje = str(error.value)
        assert '@' not in mensaje
        assert 'Cliente Prueba' not in mensaje
        assert rol in mensaje
