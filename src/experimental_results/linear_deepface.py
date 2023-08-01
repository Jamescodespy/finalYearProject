from deepface import DeepFace
from deepface.commons import functions
import cv2
import re
import requests
import json
import itertools

#iPhone Camera
source = "http://camera_2:iphone_camera@86.146.125.200:8082/video"
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
#Target size
target_size = functions.find_target_size(model_name=models[8])
#Database Path
db_path = 'src/images'

#Backend connection
cameras_json = json.loads(requests.get("http://localhost:1000/cameras").content.decode('utf-8'))['cameras']
cameras = []
for camera in cameras_json:
    connection = camera['connection']
    room_id = camera['room_id']
    cameras.append({"room_id": room_id, "capture": cv2.VideoCapture(connection)})

for camera in itertools.cycle(cameras):
    cap = camera['capture']
    if cap:
        ret, frame = cap.read()
        raw_img = frame.copy()
        try:
            # just extract the regions to highlight in webcam
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
        except:  # to avoid exception if no face detected
            faces = []

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
                        # -------------------------------
                        # extract detected face
                        custom_face = base_img[y : y + h, x : x + w]
                        dfs = DeepFace.find(
                            img_path=custom_face,
                            db_path=db_path,
                            model_name=models[8],
                            detector_backend=detector_backend,
                            distance_metric='cosine',
                            enforce_detection=False,
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

        cv2.imshow('frame', frame)
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break

#DeepFace.stream(db_path='src/images',source="http://camera_2:iphone_camera@86.146.125.200:8082/video", enable_face_analysis=False)