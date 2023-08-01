# CSC3002 - GK02: Smart Environmental Monitor and Cloud Streaming

This project is focused on solving the problem many smart security camera providers have of not providing adequate functionality when it comes to labelling in facial detection with the knock-on consequence of not being able to give movement histories for labelled individuals or tailed alert messages for their detection. 

The goal of this project is to monitor a human environment using smart remote cameras capable of detecting individuals using facial detection and facial recognition, to track the movement of individuals throughout a building, and provide live tracking and movement histories of people both known and unknown. The system should be capable of identifying and labelling new individuals and not just those trained prior to runtime. The system should provide functionality missing from many smart companies’ products, demonstrating the potential possibilities in the future of smart home security.  The project aims to utilize cloud streaming, storing all processed information in the cloud. The project also aims to investigate how different facial recognition models perform when tasked with real-time processing of faces for identification and detection purposes, and also to investigate how clustering algorithms can be used to separate out data on unknown individuals who are not known prior to runtime.


# Running the Project

To run the project:

1. Pull down the three branches - frontend, backend, and deepface
2. Dockerize the Frontend and the Backend Services using the following commands where they will automatically run within a container:

```
    docker build -t frontend-image .
    docker run -d --name frontend-container -p 3000:3000 frontend-image

    docker build -t backend-image .
    docker run -d --name backend-container -p 1000:1000 backend-image
```


3. Access the frontend service by visiting localhost:3000 in the browser
4. Add rooms, cameras, and labels through the frontend service
5. Within the deepface branch, run camera_service.py
