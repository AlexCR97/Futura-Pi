import cv2
import datetime
import glob
import numpy
import os
import src.firebase.bucket as bucket
import src.config as config


def descargar_rostros(ruta_bucket, ruta_local):
    """
    Descarga las imagenes de los rostros capturados desde Firebase Storage Bucket y las almacena en una ruta local

    :param ruta_bucket: La ruta de Firebase Storage Bucket en donde se encuentran almacenadas las imagenes de los rostros
    :type ruta_bucket: str

    :param ruta_local: La ruta local en donde se descargaran las imagenes
    :type ruta_local: str
    """
    print('Descargando imagenes...')
    bucket.descargar_imagenes(ruta_bucket, ruta_local)
    print('Imagenes descargadas!')


def generar_modelo(ruta_modelo, ruta_imagenes):
    """
    Genera el modelo de entrenamiento (.xml) para el reconocedor facial

    :param ruta_modelo: La ruta en donde se va almacenar el modelo de entrenamiento
    :type ruta_modelo: str

    :param ruta_imagenes: La ruta en donde se encuentran las imagenes para generar el modelo de entrenamiento
    :type ruta_imagenes: str
    """

    carpetas_personas = os.listdir(ruta_imagenes)
    print('carpetas_personas =', carpetas_personas)
    print()

    labels = []
    rostros = []
    contador_label = 0

    for nombre_persona in carpetas_personas:
        ruta_persona = ruta_imagenes + '/' + nombre_persona
        print('ruta_persona =', ruta_persona)
        print()

        for archivo_imagen in os.listdir(ruta_persona):
            print('imagen =', nombre_persona + '/' + archivo_imagen)

            imagen_capturada = cv2.imread(ruta_persona + '/' + archivo_imagen, 0)
            imagen_redimensionada = cv2.resize(imagen_capturada, config.dimension_estandar)
            rostros.append(imagen_redimensionada)
            labels.append(contador_label)

            cv2.imshow('Rostro capturado', imagen_redimensionada)
            cv2.waitKey(0)

        contador_label = contador_label + 1
        print()

    # Entrenar el reconocedor facial
    print("Entrenando...")
    face_recognizer = cv2.face.EigenFaceRecognizer_create()
    face_recognizer.train(rostros, numpy.array(labels))

    # Generar el nombre del modelo
    fecha = datetime.datetime.now()
    nombre_modelo = 'modelo_{}-{}-{}_{}-{}-{}.xml'.format(fecha.day, fecha.month, fecha.year, fecha.hour, fecha.minute, fecha.second)
    ruta_modelo_con_nombre = ruta_modelo + '/' + nombre_modelo

    # Generar el modelo de entenamiento
    print('Generando modelo...')
    face_recognizer.write(ruta_modelo_con_nombre)
    print("Modelo generado!")
    print()


def ultimo_modelo():
    """
    Obtiene la ruta del ultimo modelo de entrenamiento generado
    :return: str
    """
    modelos = glob.glob(config.ruta_modelos + '/*.xml')
    ultimo_archivo = max(modelos, key=os.path.getctime)
    return ultimo_archivo.replace('\\', '/')
