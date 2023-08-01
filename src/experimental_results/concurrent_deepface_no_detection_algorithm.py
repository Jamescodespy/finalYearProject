import cv2
import threading
import requests
import json
from deepface import DeepFace
import re

class camThread(threading.Thread):
    def __init__(self, room_id, connection):
        threading.Thread.__init__(self)
        self.room_id = room_id
        self.connection = connection
        self.backend = "http://localhost:1000/"
    def run(self):
        print("Starting " + self.room_id)
        camPreview(self.room_id, self.connection)

def camPreview(room_id, connection, backend):
    #models
    models = [
    "VGG-Face", 
    "Facenet", 
    "Facenet512", 
    "OpenFace", 
    "DeepFace", 
    "DeepID", 
    "ArcFace", 
    "Dlib", 
    "SFace",
    ]
    #detector
    detector_backend = "opencv"
    #Database Path
    db_path = 'src/images'
    if connection:  # try to get the first frame
        ret, frame = connection.read()
    else:
        ret = False

    while ret:
        ret, frame = connection.read()
        try:
            dfs = DeepFace.find(
                img_path=frame,
                db_path=db_path,
                model_name=models[8],
                detector_backend=detector_backend,
                distance_metric='cosine',
                enforce_detection=True,
                silent=True,
            )
            
            if len(dfs) > 0:
                # directly access 1st item because custom face is extracted already
                df = dfs[0]
                if df.shape[0] > 0:
                    candidate = df.iloc[0]
                    label = candidate["identity"]
                    label = re.search("/([^/\d]+)\d+\.", label).group(1)
                    print(label)
                else:
                    print("face detected: unrecognized individual")
                    embedding_objs = DeepFace.represent(img_path=frame, model_name=models[8])
                    embedding = embedding_objs[0]["embedding"]
                    requests.get(backend + "embedding/update?embedding=" + embedding + "&room_id=" + room_id)
        except:
            pass
        key = cv2.waitKey(20)
        if key == 27:  # exit on ESC
            break
    cv2.destroyWindow(room_id)


# Create two threads as follows
backend_address = "http://localhost:1000/"
response = json.loads(requests.get(backend_address + "cameras").content.decode('utf-8'))['cameras']
camprocesses = []
for camera in response:
     connection = cv2.VideoCapture(camera['connection'])
     room_id = camera['room_id']
     camprocesses.append(camThread(room_id, connection))

for process in camprocesses:
    process.start()
