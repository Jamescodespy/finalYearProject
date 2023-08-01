import cv2
from deepface import DeepFace
from deepface.commons import functions
import numpy as np
from sklearn.cluster import DBSCAN
from tqdm import tqdm
import time

def cluster_embeddings(embeddings, eps=0.50):
    # Convert the list of embeddings to a numpy array
    all_embeddings = np.array(embeddings)

    # Apply DBSCAN clustering to the embeddings
    dbscan = DBSCAN(metric='cosine', eps=eps)
    labels = dbscan.fit_predict(all_embeddings)

    # Return the resulting cluster labels
    return labels.tolist()

def total_clusters_detected(embeddings, eps=0.50):
    dbscan = DBSCAN(min_samples = 3, metric="cosine", eps=eps)
    clusters = dbscan.fit_predict(np.array(embeddings))
    num_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
    return num_clusters

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
target_size = functions.find_target_size(model_name=models[1])

videos = {
    #  "people_walking_in_park_high_resolution.mp4" : 4,
    #  "people_walking_in_park_low_resolution.mp4" : 4,
     "people_walking_across_road.mp4" : 2,
     "people_walking_in_office.mp4" : 2,
    #  "hat_and_mask_person.mp4": 1,
     "james_low_camera_angle.mp4" : 1,
     "james_low_camera_angle_low_resolution.mp4" : 1,
     "james_low_camera_angle_no_glasses_low_resolution.mp4" : 1,
     "indoor_security_camera.mp4" : 1,
    # "child_walking_up_stairs.mp4" : 1,
    # "nightime_lady_getting_plate.mp4" : 1,
    # "person_at_car_sunglasses.mp4" : 1,
    "person_at_door_daytime.mp4" : 1,
    "ring_footage_man_on_sofa.mp4": 1,
    "ring_footage_man_standing.mp4" : 1
}

eps_values = [1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

for video in videos.keys():
     for eps_value in eps_values:
        embeddings = []
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
                                embedding_objs = DeepFace.represent(img_path=custom_face, model_name=models[1], enforce_detection=False)
                                embedding = embedding_objs[0]["embedding"]
                                embeddings.append(embedding)
                            except Exception as e:
                                print(e)

            if (time.time() - start > 60):
                 break
        
        end = time.time()
        try:
            clusters = total_clusters_detected(embeddings, eps=eps_value)
        except:
            clusters = 0
        correct_answer = videos[video] == clusters
        if end - start < 60:
            with open("cluster_faces_hyperparams.txt", "a") as text_file:
                text_file.write("video: " + video + ", time taken: " + str(end-start) + ", embeddings found: " + str(len(embeddings)) + " eps value: " + str(eps_value) + " clusters found: " + str(clusters) + ", correct answer predicted: " + str(correct_answer) + "\n")
        else:
            with open("cluster_faces_hyperparams.txt", "a") as text_file:
                text_file.write("video: " + video + ", time taken: time limit exceeded" + ", embeddings found: " + str(len(embeddings)) + " eps value: " + str(eps_value) + " clusters found: " + str(clusters) + ", correct answer predicted: " + str(correct_answer) + "\n")