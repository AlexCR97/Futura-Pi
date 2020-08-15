import pyrebase
import src.config as config

_config = {
    'apiKey': 'AIzaSyDwTLZsafa_wOYI77GqsoHG5xPgOZKNc9g',
    'authDomain': 'facial-access-pi.firebaseapp.com',
    'databaseURL': 'https://facial-access-pi.firebaseio.com',
    'projectId': 'facial-access-pi',
    'storageBucket': 'facial-access-pi.appspot.com',
    'messagingSenderId': '926287147481',
    'appId': '1:926287147481:web:8a5b10b467cb84ab9529c8',
    'serviceAccount': config.ruta_firebase_sdk,
}

firebase = pyrebase.initialize_app(_config)
