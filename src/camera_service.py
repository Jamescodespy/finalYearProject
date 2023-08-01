import cv2
import threading
import requests
import json
from deepface import DeepFace
from deepface.commons import functions
import re
import base64
import numpy
import aiohttp
import asyncio

class camThread(threading.Thread):
    def __init__(self, room_id, connection):
        threading.Thread.__init__(self)
        self.room_id = room_id
        self.connection = connection
        self.backend = "http://localhost:1000/"
    def run(self):
        print("Starting " + self.room_id)
        asyncio.run(camPreview(self.room_id, self.connection, self.backend))

async def camPreview(room_id, connection, backend):
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
    #Database Path
    db_path = 'src/images'

    if connection:  # try to get the first frame
        ret, frame = connection.read()
    else:
        ret = False

    processed_embeddings = 0
    while ret:
        ret, frame = connection.read()
        raw_img = frame.copy()
        try:
            face_objs = DeepFace.extract_faces(
                img_path=raw_img,
                target_size=functions.find_target_size(model_name=models[1]),
                enforce_detection=True,
                detector_backend="ssd"
            )
            faces = [(face_obj['facial_area']['x'], face_obj['facial_area']['y'], face_obj['facial_area']['w'], face_obj['facial_area']['h']) for face_obj in face_objs]
        except:
            faces = []

        detected_faces = []
        for (x, y, w, h) in faces:
            detected_faces.append((x, y, w, h))
        
        for (x, y, w, h) in detected_faces:
            custom_face = raw_img[y : y + h, x : x + w]
            try:
                dfs = DeepFace.find(
                    img_path=custom_face,
                    db_path=db_path,
                    model_name=models[2],
                    detector_backend="opencv",
                    distance_metric='euclidean_l2',
                    enforce_detection=False,
                    silent=True,
                )
            except:
                dfs = []

            if dfs:
                df = dfs[0]
                if not df.empty:
                    candidate = df.iloc[0]
                    try:
                        embedding = DeepFace.represent(img_path=custom_face, model_name=models[8], detector_backend="opencv", enforce_detection=False)[0]['embedding']
                        params = {'embedding': str(embedding), "room_id": room_id}
                        if processed_embeddings % 15 == 0 and processed_embeddings != 0:
                            cv2.imwrite("face.jpg", custom_face)
                            with open("face.jpg", "rb") as f:
                                params['face'] = base64.b64encode(f.read()).decode('utf-8')
                        
                        if processed_embeddings % 50 == 0 and processed_embeddings != 0:
                            cv2.imwrite("frame.jpg", frame)
                            with open("frame.jpg", "rb") as f:
                                params['frame'] = base64.b64encode(f.read()).decode('utf-8')
                        
                        if candidate["Facenet512_euclidean_l2"] <= 0.9:
                            label = re.search("/([^/\d]+)\d+\.", candidate["identity"]).group(1)
                            params['label'] = label
                            async with aiohttp.ClientSession() as session:
                                async with session.post("http://localhost:1000/labeled_embeddings/add", json=params) as _:
                                    print(candidate["Facenet512_euclidean_l2"])
                                    print(room_id + ":" + label)
                        else:
                            async with aiohttp.ClientSession() as session:
                                async with session.post("http://localhost:1000/unlabeled_embeddings/add", json=params) as _:
                                    print(candidate["Facenet512_euclidean_l2"])
                                    print(room_id + ": unsure face")

                    except Exception as e:
                        print(room_id + ": Exception error: " + str(e))
            
                processed_embeddings+=1
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