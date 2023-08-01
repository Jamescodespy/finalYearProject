import unittest

from app import app, check_alerts
from pymongo import MongoClient
from bson import ObjectId

cluster = MongoClient("mongodb+srv://jhanna516:RhfBuGoBYrw1iwoj@cluster0.v5chlrq.mongodb.net/?retryWrites=true&w=majority")
db = cluster["GK02"]

class TestBackendService(unittest.TestCase):

    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        self.app = app.test_client()

    def tearDown(self):
        self.ctx.pop()
    
    def test_get_cameras_success(self):
        response = self.app.get('/cameras')
        data = response.get_json()
        
        self.assertEqual(response.status_code, 200)
        assert 'cameras' in data
    
    def test_update_camera_success(self):
        result = db['Cameras'].insert_one({"camera_name": "Test Camera", "connection": "https://google.com", "room_id": ObjectId("63cb017fc3ccd3d811e43ac5")})
        response = self.app.get("/cameras/update?camera_name=New Name&connection=https://yahoo.com&room_id=63cb017fc3ccd3d811e43ac5&camera_id=" + str(result.inserted_id))
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "Camera updated successfully."})
        db['Cameras'].delete_one({"camera_name": "New Name"})

    def test_update_camera_values_not_provided(self):
        response = self.app.get('/cameras/update')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Values not provided. Camera ID, new Camera Name, Connection and Room ID must all be provided."})
    
    def test_update_camera_name_already_exists(self):
        response = self.app.get('/cameras/update?camera_id=63cb22d6ceefcf1e1f44680d&room_id=63cb017fc3ccd3d811e43ac5&camera_name=room_2_camera_1&connection=https://google.com')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "A camera with that name already exists."})

    def test_update_camera_connection_already_exists(self):
        response = self.app.get('/cameras/update?camera_id=63cb22d6ceefcf1e1f44680d&room_id=63cb017fc3ccd3d811e43ac5&camera_name=room_1_camera_1&connection=http://camera_2:iphone_camera@86.146.125.200:8082/video')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "A camera with that connection already exists."})
    
    def test_update_camera_room_id_does_not_exist(self):
        response = self.app.get('/cameras/update?camera_id=63cb22d6ceefcf1e1f44680d&room_id=63cb017fc3ccd3d811e43ac0&camera_name=room_1_camera_1&connection=http://camera_2:iphone_camera@86.146.125.200:8082/video')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Room ID provided does not exist."})

    def test_remove_camera_sucess(self):
        result = db['Cameras'].insert_one({"camera_name": "Test Camera"})
        response = self.app.get('/cameras/remove?camera_id=' + str(result.inserted_id))
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "Camera deleted successfully."})
    
    def test_remove_camera_id_not_provided(self):
        response = self.app.get('/cameras/remove?camera_id=')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Camera ID not provided."})
    
    def test_remove_camera_camera_id_does_not_exist(self):
        response = self.app.get('/cameras/remove?camera_id=63cb22d6ceefcf1e1f446803')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Camera with the provided ID does not exist."})

    def test_add_room_success(self):
        response = self.app.get('/rooms/add?room_name=Living Room')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "Room added successfully"})
        db['Rooms'].delete_one({"room_name": "Living Room"})
        
    def test_add_room_name_not_provided(self):
        response = self.app.get('/rooms/add')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Room name not provided."})

    def test_add_room_already_exists(self):
        response = self.app.get('/rooms/add?room_name=Room_1')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Room already exists"})
    
    def test_update_room_success(self):
        response = self.app.get('/rooms/update?room_id=63cc2886d6d47f47df34b184&room_name=Living Room')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "Room name updated successfully."})
        db['Rooms'].find_one_and_update({"room_name": "Living Room"}, {"$set": {"room_name": "Room_2"}})
    
    def test_update_room_name_not_provided(self):
        response = self.app.get('/rooms/update?room_id=63cc2886d6d47f47df34b184&room_name=')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Value not provided. Room ID and new Room Name must all be provided."})
    
    def test_update_room_name_in_use(self):
        response = self.app.get('/rooms/update?room_id=63cc2886d6d47f47df34b184&room_name=Room_1')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "A room with that name already exists."})
    
    def test_update_room_id_does_not_exist(self):
        response = self.app.get('/rooms/update?room_id=63cc2886d6d47f47df34b180&room_name=Room_3')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Room with the provided ID does not exist."})
    
    def test_remove_room_success(self):
        result = db['Rooms'].insert_one({"room_name": "Test Room"})
        response = self.app.get('/rooms/remove?room_id=' + str(result.inserted_id))
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "Room deleted with cascading effects."})
    
    def test_remove_room_id_not_provided(self):
        response = self.app.get('/rooms/remove?room_id=')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Room ID not provided."})
    
    def test_remove_room_id_does_not_exist(self):
        response = self.app.get('/rooms/remove?room_id=63cc2886d6d47f47df34b180')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Room with the provided ID does not exist."})
    
    def test_add_label_success(self):
        response = self.app.get('/labels/add?label_name=Test')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "Label added successfully."})
        db['Labels'].delete_one({"label": "Test"})
    
    def test_add_label_label_not_provided(self):
        response = self.app.get('/labels/add?label_name=')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Value not provided. Label Name must be provided."})
    
    def test_add_label_label_already_exists(self):
        db['Labels'].insert_one({"label": "Test_Label"})
        response = self.app.get('/labels/add?label_name=Test_Label')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Label name alreast exists."})
        db['Labels'].delete_one({"label": "Test_Label"})
    
    def test_update_label_success(self):
        arguments = {"label_name" : "Test123", "image_label_id": "64588bfab3d3d55de6f8d9cc"}
        response = self.app.post('/labels/update', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "Labled successfully."})

    def test_update_label_label_not_provided(self):
        arguments = {"label_name" : ""}
        response = self.app.post('/labels/update', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Value not provided. Label name must be provided."})

    def test_track_label_success(self):
        response = self.app.get('/labels/track?label=James')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        for item in data:
            assert 'room_name' in item
            assert 'timestamp' in item

    def test_track_label_label_not_provided(self):
        response = self.app.get('/labels/track?label=')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Value not provided. Label Name must be provided."})

    def test_update_alert_success(self):
        arguments = {"label" : "Test Alert", "room_name": "Room_1"}
        response = self.app.post('/alerts/update', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "alert change successful"})
        db['Detection_Alert'].delete_one({"label": "Test Alert"})

    def test_update_alert_values_not_provided(self):
        arguments = {"label" : "", "room_name": ""}
        response = self.app.post('/alerts/update', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Values not provided. Room Name and Label must all be provided."})

    def test_update_alert_room_does_not_exist(self):
        arguments = {"label" : "Test Alert", "room_name": "Test Room"}
        response = self.app.post('/alerts/update', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Room does not exist."})

    def test_add_frame_success(self):
        response = self.app.get('/frames/add?frame=/9j/example_string')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "Frame added successfully"})
        db['Frames'].delete_one({"frame": "/9j/example_string"})
    
    def test_add_frame_frame_not_provided(self):
        response = self.app.get('/frames/add?frame=')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Values not provided. Frame must all be provided."})
    
    def test_add_frame_frame_already_exist(self):
        db['Frames'].insert_one({"frame": "/9j/example_frame"})
        response = self.app.get('/frames/add?frame=/9j/example_frame')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Frame already exists."})
        db['Frames'].delete_one({"frame": "/9j/example_frame"})

    def test_index_success(self):
        response = self.app.get('/')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        assert 'rooms' in data
        assert 'labels' in data
        assert 'label_image' in data

        for room in data['rooms']:
            assert 'cameras' in data['rooms'][room]
            assert 'labels' in data['rooms'][room]
            assert 'in_room' in data['rooms'][room]
            assert 'alerts' in data['rooms'][room]
    
    def test_add_labeled_embedding_success(self):
        arguments = {"label": "James", "room_id": "63cb017fc3ccd3d811e43ac5", "embedding": "[-0.9585565328598022, 0.17242030799388885, -0.8112679719924927, 0.5509317517280579, 0.036230310797691345, -0.12989641726016998, -0.8792802095413208, -0.4865736961364746, -0.5998173952102661, 0.6167787909507751, 0.7505743503570557, 1.4842123985290527, 1.5344762802124023, 0.5941153764724731, 0.2795531749725342, 0.0768122673034668, -1.0279279947280884, -1.0625559091567993, 0.29495203495025635, -0.26238954067230225, -0.38503724336624146, -0.3795359134674072, -0.6602365970611572, -0.1649753451347351, 0.6171102523803711, 0.40741536021232605, -0.22096696496009827, -1.0943753719329834, -0.46383434534072876, -0.21338282525539398, 0.27723050117492676, -0.3422282636165619, 1.7617716789245605, 0.3268194794654846, 0.4102569818496704, -0.42573413252830505, -0.526299774646759, 0.3922066390514374, -0.8640732765197754, -1.9078844785690308, 0.39692819118499756, 0.8821046352386475, 1.1165151596069336, 1.7224732637405396, -0.3471532464027405, -0.6439160704612732, -1.087731122970581, 0.07365184277296066, 1.7907707691192627, -0.32944127917289734, -0.13650915026664734, -0.46908700466156006, 0.8933354020118713, 0.49698057770729065, -0.010103229433298111, -0.07195869833230972, 1.5579169988632202, -1.0146404504776, -0.4444476068019867, -0.29660701751708984, -1.1894545555114746, -0.27887094020843506, 0.5449607372283936, 0.7364987134933472, -0.3876694440841675, 0.6363968253135681, -0.5879706740379333, 1.297664761543274, 1.1940553188323975, 0.35784396529197693, -0.5933554172515869, -0.5506107211112976, 0.010548101738095284, 0.792147159576416, 0.7555965185165405, 0.1641068160533905, 0.5808573365211487, 0.4659290909767151, 0.6216191053390503, 0.2865322232246399, -0.9538779258728027, 0.14179176092147827, 0.40394529700279236, 0.8052401542663574, -0.9154675006866455, -0.20091558992862701, 0.44305622577667236, 0.07145180553197861, -0.13906680047512054, 0.25449270009994507, 0.17356136441230774, 0.8183162808418274, 0.8160359263420105, -0.4464496970176697, -0.20216894149780273, 1.1221269369125366, 1.3001219034194946, 0.2995623052120209, 0.5087375640869141, 1.016791582107544, -0.39613857865333557, 0.32908910512924194, -0.9917020797729492, 0.2066834270954132, 0.4710474908351898, 0.06193482130765915, 0.15728148818016052, -1.3580923080444336, 0.02858397364616394, 0.13147960603237152, 0.6686378717422485, -0.8030629754066467, 0.025975681841373444, 0.46500059962272644, -0.10336348414421082, -1.3746984004974365, 0.5023797750473022, 0.14646847546100616, -1.0743814706802368, 1.424609899520874, -0.4239093065261841, -0.44090479612350464, 0.2230767011642456, 0.17885957658290863, -1.9981141090393066, -0.229985773563385, -0.5429369211196899, 1.526792049407959]"}
        response = self.app.post('/labeled_embeddings/add', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "Labeled Embedding added successfully."})
        db['Labeled_Embeddings'].find_one_and_delete({"embedding": [-0.9585565328598022, 0.17242030799388885, -0.8112679719924927, 0.5509317517280579, 0.036230310797691345, -0.12989641726016998, -0.8792802095413208, -0.4865736961364746, -0.5998173952102661, 0.6167787909507751, 0.7505743503570557, 1.4842123985290527, 1.5344762802124023, 0.5941153764724731, 0.2795531749725342, 0.0768122673034668, -1.0279279947280884, -1.0625559091567993, 0.29495203495025635, -0.26238954067230225, -0.38503724336624146, -0.3795359134674072, -0.6602365970611572, -0.1649753451347351, 0.6171102523803711, 0.40741536021232605, -0.22096696496009827, -1.0943753719329834, -0.46383434534072876, -0.21338282525539398, 0.27723050117492676, -0.3422282636165619, 1.7617716789245605, 0.3268194794654846, 0.4102569818496704, -0.42573413252830505, -0.526299774646759, 0.3922066390514374, -0.8640732765197754, -1.9078844785690308, 0.39692819118499756, 0.8821046352386475, 1.1165151596069336, 1.7224732637405396, -0.3471532464027405, -0.6439160704612732, -1.087731122970581, 0.07365184277296066, 1.7907707691192627, -0.32944127917289734, -0.13650915026664734, -0.46908700466156006, 0.8933354020118713, 0.49698057770729065, -0.010103229433298111, -0.07195869833230972, 1.5579169988632202, -1.0146404504776, -0.4444476068019867, -0.29660701751708984, -1.1894545555114746, -0.27887094020843506, 0.5449607372283936, 0.7364987134933472, -0.3876694440841675, 0.6363968253135681, -0.5879706740379333, 1.297664761543274, 1.1940553188323975, 0.35784396529197693, -0.5933554172515869, -0.5506107211112976, 0.010548101738095284, 0.792147159576416, 0.7555965185165405, 0.1641068160533905, 0.5808573365211487, 0.4659290909767151, 0.6216191053390503, 0.2865322232246399, -0.9538779258728027, 0.14179176092147827, 0.40394529700279236, 0.8052401542663574, -0.9154675006866455, -0.20091558992862701, 0.44305622577667236, 0.07145180553197861, -0.13906680047512054, 0.25449270009994507, 0.17356136441230774, 0.8183162808418274, 0.8160359263420105, -0.4464496970176697, -0.20216894149780273, 1.1221269369125366, 1.3001219034194946, 0.2995623052120209, 0.5087375640869141, 1.016791582107544, -0.39613857865333557, 0.32908910512924194, -0.9917020797729492, 0.2066834270954132, 0.4710474908351898, 0.06193482130765915, 0.15728148818016052, -1.3580923080444336, 0.02858397364616394, 0.13147960603237152, 0.6686378717422485, -0.8030629754066467, 0.025975681841373444, 0.46500059962272644, -0.10336348414421082, -1.3746984004974365, 0.5023797750473022, 0.14646847546100616, -1.0743814706802368, 1.424609899520874, -0.4239093065261841, -0.44090479612350464, 0.2230767011642456, 0.17885957658290863, -1.9981141090393066, -0.229985773563385, -0.5429369211196899, 1.526792049407959]})

    def test_add_labeled_embedding_values_not_provided(self):
        arguments = {"label": "", "room_id": ""}
        response = self.app.post('/labeled_embeddings/add', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Values not provided. Embedding, Room ID and Label must all be provided."})
    
    def test_add_labeled_embedding_room_id_does_not_exist(self):
        arguments = {"label": "Test", "room_id": "63cb017fc3ccd3d811e43ac0", "embedding": "[-0.9585565328598022, 0.17242030799388885, -0.8112679719924927, 0.5509317517280579, 0.036230310797691345, -0.12989641726016998, -0.8792802095413208, -0.4865736961364746, -0.5998173952102661, 0.6167787909507751, 0.7505743503570557, 1.4842123985290527, 1.5344762802124023, 0.5941153764724731, 0.2795531749725342, 0.0768122673034668, -1.0279279947280884, -1.0625559091567993, 0.29495203495025635, -0.26238954067230225, -0.38503724336624146, -0.3795359134674072, -0.6602365970611572, -0.1649753451347351, 0.6171102523803711, 0.40741536021232605, -0.22096696496009827, -1.0943753719329834, -0.46383434534072876, -0.21338282525539398, 0.27723050117492676, -0.3422282636165619, 1.7617716789245605, 0.3268194794654846, 0.4102569818496704, -0.42573413252830505, -0.526299774646759, 0.3922066390514374, -0.8640732765197754, -1.9078844785690308, 0.39692819118499756, 0.8821046352386475, 1.1165151596069336, 1.7224732637405396, -0.3471532464027405, -0.6439160704612732, -1.087731122970581, 0.07365184277296066, 1.7907707691192627, -0.32944127917289734, -0.13650915026664734, -0.46908700466156006, 0.8933354020118713, 0.49698057770729065, -0.010103229433298111, -0.07195869833230972, 1.5579169988632202, -1.0146404504776, -0.4444476068019867, -0.29660701751708984, -1.1894545555114746, -0.27887094020843506, 0.5449607372283936, 0.7364987134933472, -0.3876694440841675, 0.6363968253135681, -0.5879706740379333, 1.297664761543274, 1.1940553188323975, 0.35784396529197693, -0.5933554172515869, -0.5506107211112976, 0.010548101738095284, 0.792147159576416, 0.7555965185165405, 0.1641068160533905, 0.5808573365211487, 0.4659290909767151, 0.6216191053390503, 0.2865322232246399, -0.9538779258728027, 0.14179176092147827, 0.40394529700279236, 0.8052401542663574, -0.9154675006866455, -0.20091558992862701, 0.44305622577667236, 0.07145180553197861, -0.13906680047512054, 0.25449270009994507, 0.17356136441230774, 0.8183162808418274, 0.8160359263420105, -0.4464496970176697, -0.20216894149780273, 1.1221269369125366, 1.3001219034194946, 0.2995623052120209, 0.5087375640869141, 1.016791582107544, -0.39613857865333557, 0.32908910512924194, -0.9917020797729492, 0.2066834270954132, 0.4710474908351898, 0.06193482130765915, 0.15728148818016052, -1.3580923080444336, 0.02858397364616394, 0.13147960603237152, 0.6686378717422485, -0.8030629754066467, 0.025975681841373444, 0.46500059962272644, -0.10336348414421082, -1.3746984004974365, 0.5023797750473022, 0.14646847546100616, -1.0743814706802368, 1.424609899520874, -0.4239093065261841, -0.44090479612350464, 0.2230767011642456, 0.17885957658290863, -1.9981141090393066, -0.229985773563385, -0.5429369211196899, 1.526792049407959]"}
        response = self.app.post('/labeled_embeddings/add', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Room ID provided does not exist."})
    
    def test_add_unlabeled_embedding_success(self):
        arguments = {"room_id": "63cb017fc3ccd3d811e43ac5", "embedding": "[-0.9585565328598022, 0.17242030799388885, -0.8112679719924927, 0.5509317517280579, 0.036230310797691345, -0.12989641726016998, -0.8792802095413208, -0.4865736961364746, -0.5998173952102661, 0.6167787909507751, 0.7505743503570557, 1.4842123985290527, 1.5344762802124023, 0.5941153764724731, 0.2795531749725342, 0.0768122673034668, -1.0279279947280884, -1.0625559091567993, 0.29495203495025635, -0.26238954067230225, -0.38503724336624146, -0.3795359134674072, -0.6602365970611572, -0.1649753451347351, 0.6171102523803711, 0.40741536021232605, -0.22096696496009827, -1.0943753719329834, -0.46383434534072876, -0.21338282525539398, 0.27723050117492676, -0.3422282636165619, 1.7617716789245605, 0.3268194794654846, 0.4102569818496704, -0.42573413252830505, -0.526299774646759, 0.3922066390514374, -0.8640732765197754, -1.9078844785690308, 0.39692819118499756, 0.8821046352386475, 1.1165151596069336, 1.7224732637405396, -0.3471532464027405, -0.6439160704612732, -1.087731122970581, 0.07365184277296066, 1.7907707691192627, -0.32944127917289734, -0.13650915026664734, -0.46908700466156006, 0.8933354020118713, 0.49698057770729065, -0.010103229433298111, -0.07195869833230972, 1.5579169988632202, -1.0146404504776, -0.4444476068019867, -0.29660701751708984, -1.1894545555114746, -0.27887094020843506, 0.5449607372283936, 0.7364987134933472, -0.3876694440841675, 0.6363968253135681, -0.5879706740379333, 1.297664761543274, 1.1940553188323975, 0.35784396529197693, -0.5933554172515869, -0.5506107211112976, 0.010548101738095284, 0.792147159576416, 0.7555965185165405, 0.1641068160533905, 0.5808573365211487, 0.4659290909767151, 0.6216191053390503, 0.2865322232246399, -0.9538779258728027, 0.14179176092147827, 0.40394529700279236, 0.8052401542663574, -0.9154675006866455, -0.20091558992862701, 0.44305622577667236, 0.07145180553197861, -0.13906680047512054, 0.25449270009994507, 0.17356136441230774, 0.8183162808418274, 0.8160359263420105, -0.4464496970176697, -0.20216894149780273, 1.1221269369125366, 1.3001219034194946, 0.2995623052120209, 0.5087375640869141, 1.016791582107544, -0.39613857865333557, 0.32908910512924194, -0.9917020797729492, 0.2066834270954132, 0.4710474908351898, 0.06193482130765915, 0.15728148818016052, -1.3580923080444336, 0.02858397364616394, 0.13147960603237152, 0.6686378717422485, -0.8030629754066467, 0.025975681841373444, 0.46500059962272644, -0.10336348414421082, -1.3746984004974365, 0.5023797750473022, 0.14646847546100616, -1.0743814706802368, 1.424609899520874, -0.4239093065261841, -0.44090479612350464, 0.2230767011642456, 0.17885957658290863, -1.9981141090393066, -0.229985773563385, -0.5429369211196899, 1.526792049407959]"}
        response = self.app.post('/unlabeled_embeddings/add', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {"error": False, "message": "Unlabeled Embedding added to unlabeled collection successfully."})
        db['Labeled_Embeddings'].find_one_and_delete({"embedding": [-0.9585565328598022, 0.17242030799388885, -0.8112679719924927, 0.5509317517280579, 0.036230310797691345, -0.12989641726016998, -0.8792802095413208, -0.4865736961364746, -0.5998173952102661, 0.6167787909507751, 0.7505743503570557, 1.4842123985290527, 1.5344762802124023, 0.5941153764724731, 0.2795531749725342, 0.0768122673034668, -1.0279279947280884, -1.0625559091567993, 0.29495203495025635, -0.26238954067230225, -0.38503724336624146, -0.3795359134674072, -0.6602365970611572, -0.1649753451347351, 0.6171102523803711, 0.40741536021232605, -0.22096696496009827, -1.0943753719329834, -0.46383434534072876, -0.21338282525539398, 0.27723050117492676, -0.3422282636165619, 1.7617716789245605, 0.3268194794654846, 0.4102569818496704, -0.42573413252830505, -0.526299774646759, 0.3922066390514374, -0.8640732765197754, -1.9078844785690308, 0.39692819118499756, 0.8821046352386475, 1.1165151596069336, 1.7224732637405396, -0.3471532464027405, -0.6439160704612732, -1.087731122970581, 0.07365184277296066, 1.7907707691192627, -0.32944127917289734, -0.13650915026664734, -0.46908700466156006, 0.8933354020118713, 0.49698057770729065, -0.010103229433298111, -0.07195869833230972, 1.5579169988632202, -1.0146404504776, -0.4444476068019867, -0.29660701751708984, -1.1894545555114746, -0.27887094020843506, 0.5449607372283936, 0.7364987134933472, -0.3876694440841675, 0.6363968253135681, -0.5879706740379333, 1.297664761543274, 1.1940553188323975, 0.35784396529197693, -0.5933554172515869, -0.5506107211112976, 0.010548101738095284, 0.792147159576416, 0.7555965185165405, 0.1641068160533905, 0.5808573365211487, 0.4659290909767151, 0.6216191053390503, 0.2865322232246399, -0.9538779258728027, 0.14179176092147827, 0.40394529700279236, 0.8052401542663574, -0.9154675006866455, -0.20091558992862701, 0.44305622577667236, 0.07145180553197861, -0.13906680047512054, 0.25449270009994507, 0.17356136441230774, 0.8183162808418274, 0.8160359263420105, -0.4464496970176697, -0.20216894149780273, 1.1221269369125366, 1.3001219034194946, 0.2995623052120209, 0.5087375640869141, 1.016791582107544, -0.39613857865333557, 0.32908910512924194, -0.9917020797729492, 0.2066834270954132, 0.4710474908351898, 0.06193482130765915, 0.15728148818016052, -1.3580923080444336, 0.02858397364616394, 0.13147960603237152, 0.6686378717422485, -0.8030629754066467, 0.025975681841373444, 0.46500059962272644, -0.10336348414421082, -1.3746984004974365, 0.5023797750473022, 0.14646847546100616, -1.0743814706802368, 1.424609899520874, -0.4239093065261841, -0.44090479612350464, 0.2230767011642456, 0.17885957658290863, -1.9981141090393066, -0.229985773563385, -0.5429369211196899, 1.526792049407959]})
    
    def test_add_unlabeled_embedding_values_not_provided(self):
        arguments = {"label": "", "room_id": ""}
        response = self.app.post('/unlabeled_embeddings/add', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Values not provided. Embedding and Room ID must all be provided."})
    
    def test_add_unlabeled_embedding_room_id_does_not_exist(self):
        arguments = {"label": "Test", "room_id": "63cb017fc3ccd3d811e43ac0", "embedding": "[-0.9585565328598022, 0.17242030799388885, -0.8112679719924927, 0.5509317517280579, 0.036230310797691345, -0.12989641726016998, -0.8792802095413208, -0.4865736961364746, -0.5998173952102661, 0.6167787909507751, 0.7505743503570557, 1.4842123985290527, 1.5344762802124023, 0.5941153764724731, 0.2795531749725342, 0.0768122673034668, -1.0279279947280884, -1.0625559091567993, 0.29495203495025635, -0.26238954067230225, -0.38503724336624146, -0.3795359134674072, -0.6602365970611572, -0.1649753451347351, 0.6171102523803711, 0.40741536021232605, -0.22096696496009827, -1.0943753719329834, -0.46383434534072876, -0.21338282525539398, 0.27723050117492676, -0.3422282636165619, 1.7617716789245605, 0.3268194794654846, 0.4102569818496704, -0.42573413252830505, -0.526299774646759, 0.3922066390514374, -0.8640732765197754, -1.9078844785690308, 0.39692819118499756, 0.8821046352386475, 1.1165151596069336, 1.7224732637405396, -0.3471532464027405, -0.6439160704612732, -1.087731122970581, 0.07365184277296066, 1.7907707691192627, -0.32944127917289734, -0.13650915026664734, -0.46908700466156006, 0.8933354020118713, 0.49698057770729065, -0.010103229433298111, -0.07195869833230972, 1.5579169988632202, -1.0146404504776, -0.4444476068019867, -0.29660701751708984, -1.1894545555114746, -0.27887094020843506, 0.5449607372283936, 0.7364987134933472, -0.3876694440841675, 0.6363968253135681, -0.5879706740379333, 1.297664761543274, 1.1940553188323975, 0.35784396529197693, -0.5933554172515869, -0.5506107211112976, 0.010548101738095284, 0.792147159576416, 0.7555965185165405, 0.1641068160533905, 0.5808573365211487, 0.4659290909767151, 0.6216191053390503, 0.2865322232246399, -0.9538779258728027, 0.14179176092147827, 0.40394529700279236, 0.8052401542663574, -0.9154675006866455, -0.20091558992862701, 0.44305622577667236, 0.07145180553197861, -0.13906680047512054, 0.25449270009994507, 0.17356136441230774, 0.8183162808418274, 0.8160359263420105, -0.4464496970176697, -0.20216894149780273, 1.1221269369125366, 1.3001219034194946, 0.2995623052120209, 0.5087375640869141, 1.016791582107544, -0.39613857865333557, 0.32908910512924194, -0.9917020797729492, 0.2066834270954132, 0.4710474908351898, 0.06193482130765915, 0.15728148818016052, -1.3580923080444336, 0.02858397364616394, 0.13147960603237152, 0.6686378717422485, -0.8030629754066467, 0.025975681841373444, 0.46500059962272644, -0.10336348414421082, -1.3746984004974365, 0.5023797750473022, 0.14646847546100616, -1.0743814706802368, 1.424609899520874, -0.4239093065261841, -0.44090479612350464, 0.2230767011642456, 0.17885957658290863, -1.9981141090393066, -0.229985773563385, -0.5429369211196899, 1.526792049407959]"}
        response = self.app.post('/unlabeled_embeddings/add', json=arguments)
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data, {"error": True, "message": "Room ID provided does not exist."})
    
    async def test_check_alert(self):
        db['Detection_Alert'].insert_one({"room_id": "63cb017fc3ccd3d811e43ac5", "label": "Test Alert"})
        response = await check_alerts("James", "63cb017fc3ccd3d811e43ac5")
        self.assertEqual(response, "message sent")
        db['Detection_Alert'].delete_one({"room_id": "63cb017fc3ccd3d811e43ac5", "label": "Test Alert"})
    
if __name__ == '__main__':
    unittest.main()