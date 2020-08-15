import pathlib

_ruta_proyecto = pathlib.Path(__file__).parent.parent.absolute()

ruta_proyecto = str(_ruta_proyecto).replace('\\', '/')
ruta_img = ruta_proyecto + '/assets/img'
ruta_img_entrenamiento = ruta_img + '/entrenamiento'
ruta_img_capturados = ruta_img + '/capturados'
ruta_modelos = ruta_proyecto + '/assets/models'
ruta_registros = ruta_proyecto + '/assets/registros'
ruta_firebase_sdk = ruta_proyecto + '/src/firebase/service-account.json'

dimension_estandar_w = 150
dimension_estandar_h = 150
dimension_estandar = (dimension_estandar_w, dimension_estandar_h)

dimension_ventana_w = 640
dimension_ventana_h = 580
dimension_ventana = (dimension_ventana_w, dimension_ventana_h)

dias = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miercoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sabado',
    6: 'Domingo',
}

meses = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre',
}


def fecha_str(date):
    return '{}, {}/{}/{}'.format(dias[date.weekday()], date.day, meses[date.month], date.year)


def hora_str(date):
    return '{}:{}:{}'.format(date.hour, date.minute, date.second)


