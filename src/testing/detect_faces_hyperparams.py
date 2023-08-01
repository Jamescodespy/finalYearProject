import cv2
from deepface import DeepFace
from deepface.commons import functions
from tqdm import tqdm
import time

#detector
detector_backends = [
    "retinaface",
    "mtcnn",
    "opencv",
    "ssd",
    "dlib"
]

#Database Path
db_path = 'src/images'

#Target size
target_sizes = [
    "VGG-Face",
    "Facenet",
    "Facenet512",
    "OpenFace",
    "DeepFace",
    "DeepID",
    "Dlib",
    "ArcFace",
    "SFace"
]

videos = [
     "people_walking_in_park_high_resolution.mp4",
     "people_walking_in_park_low_resolution.mp4",
     "people_walking_across_road.mp4",
     "people_walking_in_office.mp4",
     "hat_and_mask_person.mp4",
     "james_low_camera_angle_high_resolution.mp4",
     "james_low_camera_angle_low_resolution.mp4",
     "james_low_camera_angle_no_glasses_low_resolution.mp4",
     "indoor_security_camera.mp4"
    "child_walking_up_stairs.mp4",
    "nightime_lady_getting_plate.mp4",
    "person_at_car_sunglasses.mp4",
    "person_at_door_daytime.mp4",
    "ring_footage_man_on_sofa.mp4",
    "ring_footage_man_standing.mp4"
]

for video in videos:
    for target_size in target_sizes:
        for detector_backend in detector_backends:
            total_face_count = 0
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
                        target_size= functions.find_target_size(model_name=target_size),
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
                        total_face_count+=1
                    
                    if(time.time() - start > 60):
                        break
                except Exception as e:
                    pass
            end = time.time()
            if end - start < 120:
                with open("detect_faces_hyperparams.txt", "a") as text_file:
                    text_file.write("video: " + video + ", backend detector: " + detector_backend + ", target size: " + target_size + ", time taken: " + str(end-start) + ", faces detected: " + str(total_face_count) + "\n")
            else:
                with open("detect_faces_hyperparams.txt", "a") as text_file:
                    text_file.write("video: " + video + ", backend detector: " + detector_backend + ", target size: " + target_size + ", time limit exceeded" + "\n")