import cv2
from deepface import DeepFace
from deepface.commons import functions
from tqdm import tqdm
import time
import re
#detector
detector_backends = [
    "ssd",
    # "opencv",
    # "retinaface",
    "mtcnn",
    # "dlib"
]

#models
models = [
    # "Dlib",
    # "DeepID",
    # "Ensemble",
    "ArcFace",
    "SFace",
    "Facenet512", 
    "OpenFace", 
    "DeepFace", 
    "VGG-Face", 
    "Facenet", 
]

#Database Path
db_path = 'src/images'

videos = [
     "james_low_camera_angle_no_glasses_low_resolution.mp4",
     "james_low_camera_angle.mp4",
     "james_low_camera_angle_low_resolution.mp4",  
]

candidate_scores = [ 1.1, 1.05, 1.0, 0.95, 0.9]
for video in videos:
    for detector_backend in detector_backends:
        for model in models:
            for candidate_score in candidate_scores:
                james_detections = 0
                empty_dataframe = 0
                incorrect_detections = 0
                start = time.time()
                cap = cv2.VideoCapture('src/videos/' + video)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                # Check if video is opened successfully
                if not cap.isOpened():
                    print("Error opening video stream or file")

                # Loop through each frame of the video
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                for i in range(total_frames):
                    # Read the frame
                    ret, frame = cap.read()
                    raw_img = frame.copy()

                    try:
                        face_objs = DeepFace.extract_faces(
                            img_path=frame,
                            target_size=functions.find_target_size("Facenet"),
                            detector_backend="ssd",
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
                    except Exception as e:
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
                                    try:
                                        dfs = DeepFace.find(
                                            img_path=custom_face,
                                            db_path=db_path,
                                            model_name=model,
                                            detector_backend=detector_backend,
                                            distance_metric='euclidean_l2',
                                            enforce_detection=False,
                                            silent=True,
                                        )
                                    except Exception as e:
                                        print(e)
                                        dfs = []

                                    if dfs:
                                        df = dfs[0]
                                        if not df.empty:
                                            candidate = df.iloc[0]
                                            try:
                                                label = re.search("/([^/\d]+)\d+\.", candidate["identity"]).group(1)
                                                if candidate[model + "_euclidean_l2"] <= candidate_score:
                                                    if label == "James":
                                                         james_detections +=1
                                                    else:
                                                        incorrect_detections += 1
                                            except Exception as e:
                                                print("Exception error: " + str(e))
                                        else:
                                            empty_dataframe+=1
         
                        if(time.time() - start > 60):
                            break

                end = time.time()
                if end - start < 60:
                    with open("extract_faces_hyperparams.txt", "a") as text_file:
                        text_file.write("video: " + video + ", backend detector: " + detector_backend + ", model_name: " + model + ", candidate score: "+ str(candidate_score) + ", time taken: " + str(end-start) + ", correct detections: " + str(james_detections) + ", incorrect detections: " + str(incorrect_detections) + ", no detections: " + str(empty_dataframe) + "\n")
                else:
                    with open("extract_faces_hyperparams.txt", "a") as text_file:
                        text_file.write("video: " + video + ", backend detector: " + detector_backend + ", model_name: " + model + ", candidate score: "+ str(candidate_score) +  ", time limit exceeded" + ", correct detections: " + str(james_detections) + ", incorrect detections: " + str(incorrect_detections) + ", no detections: " + str(empty_dataframe) + "\n")                    

                    
                    
                