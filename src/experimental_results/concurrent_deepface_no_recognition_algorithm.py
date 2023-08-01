import cv2
import threading
import requests
import json
from deepface import DeepFace
from deepface.commons import functions
import numpy as np
from sklearn.cluster import DBSCAN

class camThread(threading.Thread):
    def __init__(self, room_id, connection):
        threading.Thread.__init__(self)
        self.room_id = room_id
        self.connection = connection
        self.backend = "http://localhost:1000/"
    def run(self):
        print("Starting " + self.room_id)
        camPreview(self.room_id, self.connection, self.backend)

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
    detector_backend = "ssd"
    #Database Path
    db_path = 'src/images'
    #Target size
    target_size = functions.find_target_size(model_name=models[8])
    #Embedding Counter
    embeddings = []
    if connection:  # try to get the first frame
        ret, frame = connection.read()
    else:
        ret = False

    while ret:
        ret, frame = connection.read()
        raw_img = frame.copy()
        try:
            face_objs = DeepFace.extract_faces(
               img_path=frame,
               target_size=target_size,
               detector_backend=detector_backend,
               enforce_detection=True,
            )
            faces = []
            for face_obj in face_objs:
                facial_area = face_obj["facial_area"]
                faces.append(
                    (
                        facial_area["x"],
                        facial_area["y"],
                        facial_area["w"],
                        facial_area["h"],
                    )
                )
        except:
            faces = []
        
        base_img = frame.copy()
        detected_faces = []
        for x, y, w, h in faces:
            detected_faces.append((x, y, w, h))
            detected_faces_final = detected_faces.copy()
            base_img = raw_img.copy()

            for detected_face in detected_faces_final:
                        x = detected_face[0]
                        y = detected_face[1]
                        w = detected_face[2]
                        h = detected_face[3]
                        # ---------------------
                        # extract detected face
                        custom_face = base_img[y : y + h, x : x + w]
                        try:
                            embedding_objs = DeepFace.represent(img_path=custom_face, model_name=models[8], enforce_detection=False)
                            embedding = embedding_objs[0]["embedding"]
                            embeddings.append(embedding)
                            
                        except Exception as e:
                            print(e)

def cluster_embeddings(embeddings, eps=0.55):
    dbscan = DBSCAN(metric="cosine", eps=eps)
    clusters = dbscan.fit_predict(np.array(embeddings))
    last_label = clusters[-1]
    return last_label


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