import cv2
import datetime
import glob
import json
import os
import pathlib
import src.config as config
import src.opencv.gui as gui
import src.firebase.bucket as bucket
import src.firebase.database as database
import threading

_reconocedor = cv2.face.EigenFaceRecognizer_create()
_clasificador = cv2.CascadeClassifier('{}haarcascade_frontalface_default.xml'.format(cv2.data.haarcascades))
_confianza_base = 5700

_ruta_modelo = ''     # El archivo .xml obtenido del entrenamiento de rostros
_ruta_registros = ''  # El archivo .txt en donde se guardaran los regisros locales
_ruta_imagenes = ''   # La ruta donde estan guardadas las imagenes de los usuarios
_ruta_imagenes_ids =  None  # La lista de personas

_ESTADO_ESPERA = 1
_ESTADO_CAPTURANDO_ROSTRO = 2
_ESTADO_CAPTURAR_ROSTRO = 3
_ESTADO_PERMITIR_ACCESO = 4
_ESTADO_DENEGAR_ACCESO = 5
_ESTADO_ROSTRO_NO_CAPTURADO = 6
_estado = _ESTADO_ESPERA
#_estado = _ESTADO_PERMITIR_ACCESO
#_estado = _ESTADO_DENEGAR_ACCESO

_persona_capturada = {  # El objeto que se va a registar en firebase
    'uid': '',
    'fecha': '',
    'hora': '',
    'permitir_acceso': False,
}


def inicializar(ruta_modelo, ruta_registros, ruta_imagenes):
    """
    Inicializa el reconocedor facial con el modelo de entrenamiento y las imagenes resultado del entrenamiento

    :param ruta_modelo: La ruta del modelo de entrenamiento (el archivo .xml generado por el entrenador)
    :type ruta_modelo: str

    :param ruta_registros: La ruta del registro local en donde se guardaran las personas capturadas
    :type ruta_registros: str

    :param ruta_imagenes: La ruta de las imagenes generadas por el entrenador
    :type ruta_imagenes: str
    """
    global _ruta_modelo, _ruta_registros, _ruta_imagenes, _ruta_imagenes_ids
    _ruta_modelo = ruta_modelo
    _ruta_registros = ruta_registros
    _ruta_imagenes = ruta_imagenes
    _ruta_imagenes_ids = os.listdir(_ruta_imagenes)

    _reconocedor.read(_ruta_modelo)

    # Inicializar botones
    global _botones

    x_pos = gui.margin_botones
    y_pos = gui.margin_botones
    _botones.append(gui.Boton(x_pos, y_pos, 'Entrenar', _on_click_entrenar, (255, 0, 0)))

    x_pos = x_pos + gui.dim_boton_w + gui.margin_botones
    y_pos = gui.margin_botones
    _botones.append(gui.Boton(x_pos, y_pos, 'Iniciar', _on_click_iniciar, (0, 255, 0)))

    x_pos = x_pos + gui.dim_boton_w + gui.margin_botones
    y_pos = gui.margin_botones
    _botones.append(gui.Boton(x_pos, y_pos, 'Subir datos', _on_click_subir_datos, (0, 0, 255)))


def iniciar():
    global _estado

    # Configuraciones de la ventana
    window_name = 'FuturaPi'
    cv2.namedWindow(window_name)
    cv2.moveWindow(window_name, 400, 100)
    cv2.setMouseCallback(window_name, _on_mouse_click)

    # Iniciar camara
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        # Detectamos los rostros en la imagen
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        aux_frame = gray.copy()
        faces = _clasificador.detectMultiScale(gray, 1.3, 5)

        # La aplicacion esta esperando a detectar un rostro para iniciar con la captura
        if _estado == _ESTADO_ESPERA:
            if len(faces) != 0:
                _timer_capturando_rostro.start()
                _estado = _ESTADO_CAPTURANDO_ROSTRO

        # La aplicacion ha detectado un rostro e inicia una cuenta regresiva para realizar la captura
        elif _estado == _ESTADO_CAPTURANDO_ROSTRO:
            posicion = (int(config.dimension_ventana_w / 2), int(config.dimension_ventana_h / 2))
            cv2.putText(frame, str(_cuenta_regresiva_capturando_rostro), posicion, 2, 3, (0, 255, 0), 1, cv2.LINE_AA)
            pass

        # La aplicacion captura el rostro para saber si permitir o denegar el acceso
        elif _estado == _ESTADO_CAPTURAR_ROSTRO:

            # Se detecto un rostro
            if len(faces) != 0:
                for (x, y, w, h) in faces:
                    rostro = aux_frame[y:y + h, x:x + w]
                    rostro = cv2.resize(rostro, config.dimension_estandar, interpolation=cv2.INTER_CUBIC)

                    resultado = _reconocedor.predict(rostro)
                    id_persona = resultado[0]
                    confianza = resultado[1]
                    date = datetime.datetime.now()

                    # Capturar los datos
                    _persona_capturada['uid'] = id_persona
                    _persona_capturada['fecha'] = config.fecha_str(date)
                    _persona_capturada['hora'] = config.hora_str(date)

                    # El rostro fue reconocido, capturarlo, subirlo a Firebase (en otro thread) y permitir el acceso
                    if confianza < _confianza_base:
                        _persona_capturada['permitir_acceso'] = True

                        fecha = datetime.datetime.now()
                        nombre_captura = 'captura_{}-{}-{}_{}-{}-{}.jpg'.format(fecha.day, fecha.month, fecha.year, fecha.hour, fecha.minute, fecha.second)
                        ruta_captura = '{}/{}'.format(config.ruta_img_capturados, id_persona)
                        ruta_captura_con_nombre = ruta_captura + '/' + nombre_captura
                        pathlib.Path(ruta_captura).mkdir(parents=True, exist_ok=True)
                        print('Guardando imagen del rostro capturado en', ruta_captura_con_nombre)
                        cv2.imwrite(ruta_captura_con_nombre, rostro)
                        print('Agregando persona al registro local', _ruta_registros)
                        agregar_registro(_ruta_registros, _persona_capturada)

                        _estado = _ESTADO_PERMITIR_ACCESO

                    # El rostro no fue reconocido, denegar acceso
                    else:
                        _persona_capturada['permitir_acceso'] = False
                        _estado = _ESTADO_DENEGAR_ACCESO

            # No se detecto ningun rostro, mostrar mensaje de error
            else:
                #_timer_mostrar_resultado.start()
                _estado = _ESTADO_ROSTRO_NO_CAPTURADO

        # La aplicacion ha reconocido el rostro y mostrara los resultados en pantalla
        elif _estado == _ESTADO_PERMITIR_ACCESO:
            print('Rostro reconocido :D Permitir acceso')

            # Variables del fondo
            fondo_margin = 55
            fondo_x1 = fondo_margin
            fondo_y1 = fondo_margin
            fondo_x2 = config.dimension_ventana_w - fondo_margin
            fondo_y2 = config.dimension_ventana_h - (fondo_margin * 2)

            # Dibujar fondo para leer mejor el texto
            cv2.rectangle(frame, (fondo_x1, fondo_y1), (fondo_x2, fondo_y2), (30, 30, 30), -1)

            # Variables de texto
            color_text = (250, 250, 250)
            margin_left = 75
            margin_bottom = 40
            font_scale = 0.60

            # Mensaje: Permitir acceso
            x_pos = margin_left
            y_pos = int(fondo_margin * 2.25)
            cv2.putText(frame, "Acceso permitido", (x_pos, y_pos), 2, 1.8, (0, 255, 0), 1, cv2.LINE_AA)

            # Dato: Nombre de la persona detectada
            x_pos = margin_left
            y_pos = y_pos + margin_bottom
            cv2.putText(frame, 'Persona identificada', (x_pos, y_pos), 2, font_scale, color_text, 1, cv2.LINE_AA)

            x_pos = int(config.dimension_ventana_w / 2)
            y_pos = y_pos
            cv2.putText(frame, 'Castillo, Alejandro', (x_pos, y_pos), 2, font_scale, color_text, 1, cv2.LINE_AA)

            # Dato: Fecha de captura
            x_pos = margin_left
            y_pos = y_pos + margin_bottom
            cv2.putText(frame, 'Fecha de captura', (x_pos, y_pos), 2, font_scale, color_text, 1, cv2.LINE_AA)

            x_pos = int(config.dimension_ventana_w / 2)
            y_pos = y_pos
            cv2.putText(frame, _persona_capturada['fecha'], (x_pos, y_pos), 2, font_scale, color_text, 1, cv2.LINE_AA)

            # Dato: Hora de captura
            x_pos = margin_left
            y_pos = y_pos + margin_bottom
            cv2.putText(frame, 'Hora de captura', (x_pos, y_pos), 2, font_scale, color_text, 1, cv2.LINE_AA)

            x_pos = int(config.dimension_ventana_w / 2)
            y_pos = y_pos
            cv2.putText(frame, _persona_capturada['hora'], (x_pos, y_pos), 2, font_scale, color_text, 1, cv2.LINE_AA)
            pass

        # La aplicacion no ha reconocido el rostro y mostrar los resultados en pantalla
        elif _estado == _ESTADO_DENEGAR_ACCESO:
            # Variables del fondo
            fondo_margin = 55
            fondo_x1 = fondo_margin
            fondo_y1 = fondo_margin
            fondo_x2 = config.dimension_ventana_w - fondo_margin
            fondo_y2 = config.dimension_ventana_h - (fondo_margin * 2)

            # Dibujar fondo para leer mejor el texto
            cv2.rectangle(frame, (fondo_x1, fondo_y1), (fondo_x2, fondo_y2), (30, 30, 30), -1)

            # Variables de texto
            margin_left = 75

            # Mensaje: Denegar acceso
            x_pos = margin_left
            y_pos = int(fondo_margin * 2.25)
            cv2.putText(frame, "Acceso denegado", (x_pos, y_pos), 2, 1.8, (0, 0, 255), 1, cv2.LINE_AA)

        # La aplicacion no ha podido capturar el rostro, entonces muestra un mensaje de error
        elif _estado == _ESTADO_ROSTRO_NO_CAPTURADO:
            pass

        # Sin importar el estado de la aplicacion, capturar los rostros detectados
        for (x, y, w, h) in faces:
            rostro = aux_frame[y:y+h, x:x+w]
            rostro = cv2.resize(rostro, config.dimension_estandar, interpolation=cv2.INTER_CUBIC)

            resultado = _reconocedor.predict(rostro)
            id_persona = resultado[0]
            confianza = resultado[1]

            # Por defecto, suponemos que el rostro es deconocido
            mensaje = 'Desconocido'
            color = (0, 0, 255)

            # En caso de sea reconocido, cambiamos los valores a mostrar
            if confianza < _confianza_base:
                #print('id_persona:', id_persona)
                #print('_ruta_imagenes_ids:', _ruta_imagenes_ids)

                mensaje = _ruta_imagenes_ids[id_persona]
                color = (0, 255, 0)

            # Mostramos el resultado
            #cv2.putText(frame, mensaje, (x, y - 25), 2, 1, color, 1, cv2.LINE_AA) // No es necesario mostrar el nombre de la persona
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        # Dibujar botones
        for boton in _botones:
            cv2.rectangle(frame, boton.top_left, boton.bottom_right, boton.color, -1)
            cv2.putText(frame, boton.text, boton.bottom_left, 2, 0.50, (0, 0, 0), 1, cv2.LINE_AA)

        # Mostrar el estado actual
        ##print('_estado =', _estado)
        mensaje = 'Esperando un rostro...'
        if _estado == _ESTADO_DENEGAR_ACCESO:
            mensaje = 'Denegar acceso'
        elif _estado == _ESTADO_PERMITIR_ACCESO:
            mensaje = 'Permitir acceso'
        elif _estado == _ESTADO_CAPTURAR_ROSTRO:
            mensaje = 'Capturar rostro'
        elif _estado == _ESTADO_ROSTRO_NO_CAPTURADO:
            mensaje = 'Rostro no capturado'
        elif _estado == _ESTADO_CAPTURANDO_ROSTRO:
            mensaje = 'Capturando rostro'

        cv2.putText(frame, mensaje, (10, int(config.dimension_ventana_h/2)), 2, 0.75, (255, 0, 0), 1, cv2.LINE_AA)

        # Mostrar imagen y checar si se presiono la tecla ESC
        cv2.imshow(window_name, frame)
        tecla = cv2.waitKey(1)
        if tecla == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# Timer para mostrar la cuenta regresiva para capturar el rostro
def _on_timer_tick_capturando_rostro():
    global _estado, _timer_capturando_rostro, _cuenta_regresiva_capturando_rostro

    print('_on_timer_tick_capturar_rostro()')
    print('_cuenta_regresiva =', _cuenta_regresiva_capturando_rostro)
    print()

    _cuenta_regresiva_capturando_rostro -= 1

    # Si la cuenta no ha llegado a cero, sigue disminuyendo la cuenta
    if _cuenta_regresiva_capturando_rostro > 0:
        _timer_capturando_rostro = threading.Timer(1, _on_timer_tick_capturando_rostro)
        _timer_capturando_rostro.daemon = True
        _timer_capturando_rostro.start()

    # Si la cuenta ya llego a cero, capturar el rostro
    else:
        _timer_capturando_rostro = threading.Timer(1, _on_timer_tick_capturando_rostro)
        _cuenta_regresiva_capturando_rostro = 3
        _estado = _ESTADO_CAPTURAR_ROSTRO


_timer_capturando_rostro = threading.Timer(1, _on_timer_tick_capturando_rostro)
_cuenta_regresiva_capturando_rostro = 3


# Timer para mostrar los resultados de la captura de rostro
def _on_timer_tick_mostrar_resultado():
    global _estado, _timer_mostrar_resultado, _cuenta_regresiva_mostrar_resultado

    print('_on_timer_tick_mostrar_resultado()')
    print('_cuenta_regresiva_mostrar_resultado =', _cuenta_regresiva_mostrar_resultado)
    print()

    _cuenta_regresiva_mostrar_resultado -= 1

    # Si la cuenta no ha llegado a cero, sigue disminuyendo la cuenta
    if _cuenta_regresiva_mostrar_resultado > 0:
        _timer_mostrar_resultado = threading.Timer(1, _on_timer_tick_mostrar_resultado)
        _timer_mostrar_resultado.daemon = True
        _timer_mostrar_resultado.start()

    # Si la cuenta ya llego a cero, capturar el rostro
    else:
        _timer_mostrar_resultado = threading.Timer(1, _on_timer_tick_mostrar_resultado)
        _cuenta_regresiva_mostrar_resultado = 5
        _estado = _ESTADO_CAPTURAR_ROSTRO


_timer_mostrar_resultado = threading.Timer(1, _on_timer_tick_mostrar_resultado)
_cuenta_regresiva_mostrar_resultado = 5


# Metodos para el control de los registros locales

def nuevos_registros(ruta_registro):
    """
    Crea un nuevo archivo para registros locales en la ruta especificada

    :param ruta_registro: La ruta del nuevo archivo generado
    :type ruta_registro: str
    """
    fecha = datetime.datetime.now()
    nombre_registros = 'registros_{}-{}-{}_{}-{}-{}.txt'.format(fecha.day, fecha.month, fecha.year, fecha.hour, fecha.minute, fecha.second)

    with open(ruta_registro + '/' + nombre_registros, 'w') as file:
        file.write('')


def agregar_registro(ruta_registro, registro):
    """
    Agrega un registro de una persona al registro local especificado

    :param ruta_registro: La ruta del archivo de texto en donde se va a agregar el registro
    :type ruta_registro: str

    :param registro: El objeto de la persona capturada
    :type registro: dict
    """
    with open(ruta_registro, 'a') as file:
        registro_json = json.dumps(registro)
        file.write(registro_json + '\n')


def listar_registros(ruta_registros):
    """
    Parse el archivo de registros locales y lo convierte a una lista de objetos de personas capturadas

    :param ruta_registros: La ruta del archivo de texto que se va a parsear
    :type ruta_registros: str

    :return: list
    """
    with open(ruta_registros) as file:
        registros_str = file.readlines()
        registros_dict = map(lambda registro: json.loads(registro), registros_str)

    return list(registros_dict)


def ultimo_registro():
    """
    Obtiene la ruta del ultimo archivo de registros locales
    :return: str
    """
    registros = glob.glob(config.ruta_registros + '/*.txt')
    ultimo_archivo = max(registros, key=os.path.getctime)
    return ultimo_archivo.replace('\\', '/')


# Eventos de botones
_botones = []


def _on_click_entrenar():
    print('_on_click_entrenar()')


def _on_click_iniciar():
    global _estado
    _estado = _ESTADO_ESPERA


def _on_click_subir_datos():
    # Subir registros a la bd
    #print('Subiendo registros...')
    #for registro in listar_registros(_ruta_registros):
        #database.insertar_registro(registro)
    #print('Registros subidos!')

    # Subir imagenes a la bd
    for id_persona in os.listdir(config.ruta_img_capturados):
        ruta_bucket = 'Rostros/' + id_persona
        ruta_imagenes = config.ruta_img_capturados + '/' + id_persona
        print('Subiendo imagenes a', ruta_bucket)

        for ruta_imagen in os.listdir(ruta_imagenes):
            print('Subiendo imagen', ruta_imagenes + '/' + ruta_imagen)
            bucket.subir_imagen(ruta_bucket, ruta_imagen)
        print()

    print('Informacion subida a Firebase!')


def _on_mouse_click(event, x, y, flags, params):
    global _botones

    if event == cv2.EVENT_LBUTTONUP:
        for boton in _botones:
            if boton.x1 <= x <= boton.x2 and boton.y1 <= y <= boton.y2:
                boton.on_click()
