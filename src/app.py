from flask import Flask, request, jsonify
from sklearn.cluster import DBSCAN
import numpy as np
from pymongo import MongoClient, ReturnDocument
from bson import ObjectId
import ast
from datetime import datetime
from flask_cors import CORS
import discord
from discord.ext import commands
from threading import Thread

cluster = MongoClient("")
db = cluster["GK02"]

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

app = Flask(__name__)
CORS(app)

@app.route('/cameras')
def getCameras():
    camera_collection = db["Cameras"]
    cameras = list(camera_collection.find())
    cameras_list = []
    for camera in cameras:
        cameras_list.append({"_id": str(camera['_id']), "camera_name": camera['camera_name'], "room_id": str(camera['room_id']), "connection": camera['connection']})
    return jsonify({"error": False, "cameras": cameras_list}), 200


@app.route('/rooms/add')
def addRoom():
    room_name = request.args.get("room_name")
    if not room_name:
        return jsonify({"error": True, "message": "Room name not provided."}), 400

    try:
        rooms_collection = db["Rooms"]
        if rooms_collection.find_one({"room_name": room_name}):
            return jsonify({"error": True, "message" : "Room already exists"}), 400

        rooms_collection.insert_one({"room_name": room_name})
        return jsonify({"error": False, "message" : "Room added successfully"}), 200

    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@app.route('/frames/add')
def addFrame():
    frame = request.args.get('frame')
    if not frame:
        return jsonify({"error": True, "message": "Values not provided. Frame must all be provided."}), 400
    frame_collection = db["Frames"]
    existing_frame = frame_collection.find_one({"frame": frame})
    if existing_frame:
        return jsonify({"error": True, "message": "Frame already exists."}), 400
    else:
        frame_collection.insert_one({"frame": frame})
        return jsonify({"error": False, "message": "Frame added successfully"}), 200
    
@app.route('/unlabeled_embeddings/add', methods=['POST'])
async def addUnlabeledEmbedding():
    data = request.get_json()
    try:
        embedding_obj = data['embedding']
        room_id = data['room_id']
    except:
        return jsonify({"error": True, "message": "Values not provided. Embedding and Room ID must all be provided."}), 400
    frame = data.get('frame')
    face = data.get('face')
    try:
        room_collection = db["Rooms"]
        existing_room = room_collection.find_one({"_id": ObjectId(room_id)})
        if not existing_room:
            return jsonify({"error": True, "message": "Room ID provided does not exist."}), 400
        
        params = {"room_id": ObjectId(room_id)}
        if frame:
            frame_collection = db["Frames"]
            not frame_collection.find_one({"frame": frame}) and frame_collection.insert_one({"frame": frame})
            existing_frame = frame_collection.find_one({"frame": frame})['_id']
            params['frame_id'] = ObjectId(existing_frame['_id'])
        
        if face:
            face_collection = db["Faces"]
            face_collection.insert_one({"face": face})
            face_id = face_collection.find_one({"face": face})['_id']
            params["face_id"] = ObjectId(face_id)
    
        embedding_obj = ast.literal_eval(embedding_obj)
        params["embedding"] = embedding_obj
        params["timestamp"] = datetime.now()
        labeled_embedding_collection = db["Labeled_Embeddings"].find({}, {'_id': 0, "label_id": 0})
        embeddings = []
        for embedding in labeled_embedding_collection:
            embeddings.append(embedding['embedding'])
        
        embeddings.append(embedding_obj)
        embeddings = np.array(embeddings)
        dbscan = DBSCAN(metric='cosine', eps=0.3, min_samples=5)
        labels_list = dbscan.fit_predict(embeddings).tolist()

        embedding_prediction = labels_list[-1]

        matching_indices = np.where(np.array(labels_list[:-1]) == embedding_prediction)[0]
        if matching_indices.size > 0 and embedding_prediction != -1:
            first_matching_embedding = embeddings[matching_indices[0]]
            label_id = db["Labeled_Embeddings"].find_one({"embedding": first_matching_embedding.tolist()}, {'label_id': 1, '_id': 0})
            params["label_id"] = ObjectId(label_id["label_id"])
            db["Labeled_Embeddings"].insert_one(params)
            return jsonify({"error": False, "message": "Unlabeled Embedding labeled successfully."}), 200
        else:
            db["Unlabeled_Embeddings"].insert_one(params)
            await check_alerts("unknown_individuals", room_id)
            return jsonify({"error": False, "message": "Unlabeled Embedding added to unlabeled collection successfully."}), 200
        
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@app.route('/labeled_embeddings/add', methods=['POST'])
async def addLabeledEmbedding():
    data = request.get_json()
    try:
        embedding = data['embedding']
        room_id = data['room_id']
        label = data['label']
    except:
        return jsonify({"error": True, "message": "Values not provided. Embedding, Room ID and Label must all be provided."}), 400
    frame = data.get('frame')
    face = data.get('face')
    try:
        params = {"room_id": ObjectId(room_id)}
        if frame:
            frame_collection = db["Frames"]
            not frame_collection.find_one({"frame": frame}) and frame_collection.insert_one({"frame": frame})
            existing_frame = frame_collection.find_one({"frame": frame})['_id']
            params['frame_id'] = ObjectId(existing_frame['_id'])
        params["embedding"] = ast.literal_eval(embedding)
        params["timestamp"] = datetime.now()

        if face:
            face_collection = db["Faces"]
            face_collection.insert_one({"face": face})
            face_id = face_collection.find_one({"face": face})['_id']
            params["face_id"] = ObjectId(face_id)

        room_collection = db["Rooms"]
        existing_room = room_collection.find_one({"_id": ObjectId(room_id)})
        if existing_room:
            label_collection = db["Labels"]
            existing_label = label_collection.find_one({"label": label})
            params["room_id"] = ObjectId(room_id)
            if not existing_label:
                label_collection.insert_one({"label": label})
            labeled_embedding_collection = db['Labeled_Embeddings']
            existing_label = label_collection.find_one({"label": label})
            params["label_id"] = existing_label['_id']
            labeled_embedding_collection.insert_one(params)

            await check_alerts(label, room_id)
            return jsonify({"error": False, "message": "Labeled Embedding added successfully."}), 200
        else:
            return jsonify({"error": True, "message": "Room ID provided does not exist."}), 400
    
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500
    
@app.route('/cameras/add')
def addCamera():
    camera_name = request.args.get('camera_name')
    room_name = request.args.get('room_name')
    connection = request.args.get('connection')
    if not camera_name or not room_name or not connection:
        return jsonify({"error": True, "message": "Value not provided. Camera Name, Room Name and Connection must all be provided."}), 400

    try:
        camera_collection = db['Cameras']
        if camera_collection.find_one({"camera_name": camera_name}):
            return jsonify({"error": True, "message": "Camera name already exists."}), 400
        if camera_collection.find_one({"connection": connection}):
            return jsonify({"error": True, "message": "Connection already belongs to another camera."}), 400
        room_collection = db['Rooms']
        existing_room = room_collection.find_one({"room_name": room_name})
        if not existing_room:
            return jsonify({"error": True, "message": "Room name provided does not exist."}), 400

        camera_collection.insert_one({"camera_name": camera_name, "room_id": ObjectId(existing_room['_id']), "connection": connection})
        return jsonify({"error": False, "message": "Camera added successfully."}), 200

    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@app.route('/labels/add')
def addLabel():
    label_name = request.args.get('label_name')
    if not label_name:
        return jsonify({"error": True, "message": "Value not provided. Label Name must be provided."}), 400
    try:
        label_collection = db['Labels']
        if label_collection.find_one({"label": label_name}):
            return jsonify({"error": True, "message": "Label name alreast exists."}), 400
        else:
            label_collection.insert_one({"label": label_name})
            return jsonify({"error": False, "message": "Label added successfully."}), 200
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@app.route('/labels/track')
def trackLabel():
    label_name = request.args.get('label')
    if not label_name:
        return jsonify({"error": True, "message": "Value not provided. Label Name must be provided."}), 400
    try:
        label_collection = db['Labels']
        label_id = label_collection.find_one({"label": label_name}, {"_id": 1})
        rooms = db['Rooms'].find({})
        room_id_to_name = {room['_id']: room['room_name'] for room in rooms}
        result = []
        if label_id:
            labeled_embeddings = db['Labeled_Embeddings']
            embeddings = labeled_embeddings.find({"label_id": label_id['_id']}, {"timestamp": 1, "room_id": 1, "_id": 0}, sort=[('timestamp', -1)])
            for emb in embeddings:
                emb_dict = {}
                emb_dict['timestamp'] = emb['timestamp']
                emb_dict['room_name'] = room_id_to_name.get(emb['room_id'], 'Unknown')
                result.append(emb_dict)
        else:
            if "unknown person" in label_name:
                unlabeled_embeddings = db['Unlabeled_Embeddings']
                unlabeled_cluster_ID = int(label_name.split(" ")[2])
                unlabeled_embeddings_array = []
                unlabeled_embeddings_collection = unlabeled_embeddings.find({}, {'_id': 0}, sort=[('timestamp', -1)])
                for embedding in unlabeled_embeddings_collection:
                        unlabeled_embeddings_array.append(embedding['embedding'])

                unlabeled_embeddings_array = np.array(unlabeled_embeddings_array)
                dbscan = DBSCAN(metric='cosine', eps=0.3, min_samples=5)
                labels_list = dbscan.fit_predict(unlabeled_embeddings_array).tolist()

                unlabeled_embeddings_collection = unlabeled_embeddings.find({}, {'_id': 0}, sort=[('timestamp', -1)])

                index = 0
                for embedding in unlabeled_embeddings_collection:
                    if labels_list[index] == unlabeled_cluster_ID:
                        emb_dict = {}
                        emb_dict['timestamp'] = embedding['timestamp']
                        emb_dict['room_name'] = room_id_to_name.get(embedding['room_id'], 'Unknown')
                        result.append(emb_dict)
                    index+=1
            
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@app.route('/labels/update', methods=['POST'])
def updateLabels():
    data = request.get_json()
    try:
        label_name = data['label_name']
        image_label_id = ObjectId(data['image_label_id'])
    except:
        return jsonify({"error": True, "message": "Value not provided. Label name must be provided."}), 400
    
    labels_collection = db['Labels']
    existing_label = labels_collection.find_one({"label": label_name})
    if existing_label is None:
        inserted_label = labels_collection.insert_one({"label": label_name})
        existing_label = labels_collection.find_one({"_id": inserted_label.inserted_id})
    
    unlabeled_embeddings_collection = db['Unlabeled_Embeddings'].find({})
    embeddings_list = []
    index = 0

    for unlabeled_embedding in unlabeled_embeddings_collection:
        if 'frame_id' in unlabeled_embedding:
            if unlabeled_embedding['frame_id'] == image_label_id:
                 matching_embedding_in_list_pos = index

        elif 'face_id' in unlabeled_embedding:
            if unlabeled_embedding['face_id'] == image_label_id:
                matching_embedding_in_list_pos = index

        embeddings_list.append(unlabeled_embedding['embedding'])
        index+=1

    unlabeled_embeddings_array = np.array(embeddings_list)
    dbscan = DBSCAN(metric='cosine', eps=0.3, min_samples=5)
    labels_list = dbscan.fit_predict(unlabeled_embeddings_array).tolist()

    cluster_label_prediction = labels_list[matching_embedding_in_list_pos]
    unlabeled_embeddings_collection = db['Unlabeled_Embeddings'].find({})

    for index_pos, unlabeled_embedding_array in enumerate(embeddings_list):
        if labels_list[index_pos] == cluster_label_prediction:
            embedding_item = db['Unlabeled_Embeddings'].find_one_and_delete({"embedding": unlabeled_embedding_array})
            db['Labeled_Embeddings'].insert_one({"label_id": ObjectId(existing_label['_id']), "embedding": unlabeled_embedding_array, "room_id": ObjectId(embedding_item['room_id']), "timestamp": embedding_item['timestamp']})

    return jsonify({"error": False, "message": "Labled successfully."}), 200

@app.route('/rooms/remove')
def removeRoom():
    room_id = request.args.get("room_id")
    if not room_id:
        return jsonify({"error": True, "message": "Room ID not provided."}), 400
    
    try:
        room_collection = db["Rooms"]
        room = room_collection.find_one_and_delete({"_id": ObjectId(room_id)})
        if room:
            db["Cameras"].delete_many({"room_id": ObjectId(room_id)})
            db["People"].delete_many({"room_id": ObjectId(room_id)})
            return jsonify({"error": False, "message": "Room deleted with cascading effects."}), 200
        else:
            return jsonify({"error": True, "message": "Room with the provided ID does not exist."}), 400
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@app.route('/cameras/remove')
def removeCamera():
    camera_id = request.args.get("camera_id")
    if not camera_id:
        return jsonify({"error": True, "message": "Camera ID not provided."}), 400
    
    try:
        camera_collection = db["Cameras"]
        camera = camera_collection.find_one_and_delete({"_id": ObjectId(camera_id)})
        if camera:
            return jsonify({"error": False, "message": "Camera deleted successfully."}), 200
        else:
            return jsonify({"error": True, "message": "Camera with the provided ID does not exist."}), 400
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@app.route('/rooms/update')
def editRoomName():
    room_id = request.args.get('room_id')
    room_name = request.args.get('room_name')
    if not room_id or not room_name:
        return jsonify({"error": True, "message": "Value not provided. Room ID and new Room Name must all be provided."}), 400
    
    try:
        room_collection = db["Rooms"]
        existing_room = room_collection.find_one({"room_name": room_name})

        if existing_room and existing_room["_id"] != ObjectId(room_id):
            return jsonify({"error": True, "message": "A room with that name already exists."}), 400
        else:
            room = room_collection.find_one_and_update({"_id": ObjectId(room_id)}, {"$set": {"room_name": room_name}}, return_document=ReturnDocument.AFTER)
            if room:
                return jsonify({"error": False, "message": "Room name updated successfully."}), 200
            else:
                return jsonify({"error": True, "message": "Room with the provided ID does not exist."}), 400
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@app.route('/cameras/update')
def editCamera():
    camera_id = request.args.get('camera_id')
    camera_name = request.args.get('camera_name')
    connection = request.args.get('connection')
    room_id = request.args.get('room_id')
    if not camera_id or not camera_name or not connection or not room_id:
        return jsonify({"error": True, "message": "Values not provided. Camera ID, new Camera Name, Connection and Room ID must all be provided."}), 400
    try:
        room_collection = db["Rooms"]
        existing_room = room_collection.find_one({"_id": ObjectId(room_id)})
        if existing_room:
            #Check camera name is not already in use
            camera_collection = db["Cameras"]
            query_by_camera_name = camera_collection.find_one({"camera_name": camera_name})
            
            if query_by_camera_name and query_by_camera_name["_id"] != ObjectId(camera_id):
                return jsonify({"error": True, "message": "A camera with that name already exists."}), 400
            
            query_by_connection = camera_collection.find_one({"connection": connection})
            if query_by_connection and query_by_connection["_id"] != ObjectId(camera_id):
                return jsonify({"error": True, "message": "A camera with that connection already exists."}), 400
            
            camera_collection = camera_collection.find_one_and_update({"_id": ObjectId(camera_id)}, {"$set": {"camera_name": camera_name, "room_id": ObjectId(room_id), "connection": connection}}, return_document=ReturnDocument.AFTER)
            if camera_collection:
                return jsonify({"error": False, "message": "Camera updated successfully."}), 200
            else:
                return jsonify({"error": True, "message": "Camera does not exist with provided ID."}), 400
        else:
            return jsonify({"error": True, "message": "Room ID provided does not exist."}), 400
    
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@app.route('/alerts/update', methods=['POST'])
def update_alerts():
    data = request.get_json()
    room_name = data['room_name']
    label = data['label']
    if not room_name or not label:
        return jsonify({"error": True, "message": "Values not provided. Room Name and Label must all be provided."}), 400
    
    rooms_collection = db['Rooms']
    room_item = rooms_collection.find_one({"room_name": room_name})
    if not room_item:
        return jsonify({"error": True, "message": "Room does not exist."}), 400
    
    alerts_collection = db['Detection_Alert']
    existing_alert = alerts_collection.find_one({"room_id": room_item['_id'], "label": label})
    if existing_alert:
        alerts_collection.delete_one({"_id": existing_alert['_id']})
    else:
        alerts_collection.insert_one({"room_id": room_item['_id'], "label": label})
        
    return jsonify({"error": False, "message": "alert change successful"}), 200

async def check_alerts(label_name, room_id):
    alerts_collection = db['Detection_Alert']
    alert_item = alerts_collection.find_one({"label": label_name, "room_id": ObjectId(room_id)})
    if alert_item:
        room_item = db['Rooms'].find_one({"_id": ObjectId(room_id)})
        message = label_name + " has been detected within " + room_item['room_name']
        channel = bot.get_channel(1095264334915063839)
        bot.loop.create_task(channel.send(message))
        return "message sent"
    
    return

@app.route('/')
def display_data():
    rooms = db['Rooms']
    cameras = db['Cameras']
    labels = db['Labels']
    labeled_embeddings = db['Labeled_Embeddings']
    unlabeled_embeddings = db['Unlabeled_Embeddings']
    detect_alerts = db['Detection_Alert']
    result = {}
    result['rooms'] = {}
    result['label_image'] = {}
    unlabeled_embeddings_array = []
    unlabeled_embeddings_collection = unlabeled_embeddings.find({}, {'_id': 0}, sort=[('timestamp', -1)])
    for embedding in unlabeled_embeddings_collection:
            unlabeled_embeddings_array.append(embedding['embedding'])
        
    unlabeled_embeddings_array = np.array(unlabeled_embeddings_array)
    dbscan = DBSCAN(metric='cosine', eps=0.4, min_samples=5)
    labels_list = dbscan.fit_predict(unlabeled_embeddings_array).tolist()
    unique_numbers = set(labels_list)

    result_dict = {}

    for number in unique_numbers:
        result_dict[number] = labels_list.index(number)
    
    result['labels'] = []
    for label in labels.find({}, {"_id": 0, "label": 1}):
        result['labels'].append(label['label'])
    
    for room in rooms.find():
        room_dict = {}

        room_cameras = []
        for camera in cameras.find({'room_id': room['_id']} ,{'room_id': 0, '_id': 0}):
            room_cameras.append(camera)

        # add the cameras to the room dictionary
        room_dict['cameras'] = room_cameras
        room_dict['labels'] = {}
        room_dict['in_room'] = {}
        room_dict['alerts'] = {}

        unknown_individual_alert = detect_alerts.find_one({"label": "unknown_individuals", "room_id": ObjectId(room['_id'])})
        if unknown_individual_alert:
            room_dict["alerts"]['unknown_individuals'] = True
        else:
            room_dict["alerts"]['unknown_individuals'] = False

        for label in labels.find({}):
            label_id = label['_id']
            label_name = label['label']
            labeled_timestamps = []
            labels_last_detection = labeled_embeddings.find_one({"label_id": label_id}, {"timestamp": 1, "room_id": 1, "_id": 0}, sort=[('timestamp', -1)])
            if labels_last_detection and labels_last_detection['room_id'] == room['_id']:
                print(label_name)
                room_dict['in_room'][label_name] = labels_last_detection["timestamp"]
            for labeled_timestamp in labeled_embeddings.find({"label_id": label_id, "room_id": room['_id']}, {"timestamp": 1, "_id": 0}):
                labeled_timestamps.append(labeled_timestamp['timestamp'])
            
            if labeled_timestamps:
                room_dict['labels'][label_name] = labeled_timestamps
            
            detect_alerts_item = detect_alerts.find_one({"label": label_name, "room_id": ObjectId(room['_id'])})
            if detect_alerts_item:
                room_dict['alerts'][label_name] = True
            else:
                room_dict['alerts'][label_name] = False

        index = 0
    
        for unlabeled_embedding in unlabeled_embeddings.find({}, {"_id": 0}, sort=[('timestamp', -1)]):
            if labels_list[index] != -1 and unlabeled_embedding['room_id'] == room['_id']:
                if "unknown person " + str(labels_list[index]) not in room_dict['labels']:
                    room_dict['labels']["unknown person " + str(labels_list[index])] = []

                room_dict['labels']["unknown person " + str(labels_list[index])].append(unlabeled_embedding['timestamp'])

                if not result['label_image'] and ('frame_id' in unlabeled_embedding or 'face_id' in unlabeled_embedding):
                    if('frame_id' in unlabeled_embedding):
                        frame = db['Frames'].find_one({"_id": unlabeled_embedding['frame_id']})
                        result['label_image'] = {"id": str(frame['_id']), "image": frame['frame']}
                    else:
                        face = db['Faces'].find_one({"_id": unlabeled_embedding['face_id']})
                        result['label_image'] = {"id": str(face['_id']), "image": face['face']}
            index+=1
        result['rooms'][room['room_name']] = room_dict

        for unlabeled_label, embedding_index in result_dict.items():
            if unlabeled_label != -1:
                unlabeled_embeddings_collection = unlabeled_embeddings.find({}, {'_id': 0, "timestamp": 1, "room_id": 1}, sort=[('timestamp', -1)])
                unlabeled_item = unlabeled_embeddings_collection[embedding_index]
                if(unlabeled_item['room_id'] == room['_id']):
                    room_dict['in_room']["unknown person " + str(unlabeled_label)] = unlabeled_item['timestamp']
                    result['labels'].append("unknown person " + str(unlabeled_label))
   
    return jsonify(result), 200

def run_bot():
    bot.run("MTEwNDI0OTE1MjIzOTU4MzI1NA.G-6ZtH.lUE2XPDOWmaJVQDMgPPFdEE1688vnOdOoNegZs")
    
if __name__ == '__main__':
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=1000)
