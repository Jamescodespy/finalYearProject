//requirements
const express = require('express')
const app = express()
const fetch = require('node-fetch')
let nunjucks = require('nunjucks')

const flash = require('express-flash');
const session = require('express-session')
const cookieParser = require('cookie-parser')
//port
const port = 3000
const address = process.env.DATABASE_HOST || 'http://127.0.0.1:1000/';
//render engine

app.use(session({
  secret: 'my-secret',
  resave: false,
  saveUninitialized: false
}));
app.use(flash());
app.set('view engine', 'html')
app.use(cookieParser());
app.use(express.json());       
app.use(express.urlencoded({extended: true})); 

nunjucks.configure(['views/'], {
    autoescape: true,
    express: app
})

app.get('/', async (req, res) => {
  const room_data = await fetch(address)
  response_json = await room_data.json()
  res.render('index.html', {res: response_json, flash: req.flash() })
})

app.post('/rooms/add', async(req, res) => {
  const room_name = req.body.room_name;
  fetch(address + "/rooms/add?room_name=" + room_name)
  .then(async response => {
    const data = await response.json()
    if (data.error) {
      req.flash("error", data.message);
    } else {
      req.flash("success", data.message);
    }
    return res.redirect('/');
  })      
})

app.post('/cameras/add', async(req, res) => {
  const camera_name = req.body.camera_name;
  const camera_connection = req.body.camera_connection;
  const room_name = req.body.room_name;
  fetch(address + "/cameras/add?camera_name=" + camera_name + "&room_name=" + room_name + "&connection=" + camera_connection)
  .then(async response => {
    const data = await response.json()
    if (data.error) {
      req.flash("error", data.message);
    } else {
      req.flash("success", data.message);
    }
    return res.redirect('/');
  })
})

app.post('/labels/add', async(req, res) => {
  const label_name = req.body.label_name;
  fetch(address + "/labels/add?label_name=" + label_name)
  .then(async response => {
    const data = await response.json()
    if (data.error) {
      req.flash("error", data.message);
    } else {
      req.flash("success", data.message);
    }
    return res.redirect('/');
  })      
})

app.post('/labels/update', async(req, res) => {
  const label_name = req.body.label_name;
  const image_label_id = req.body.image_label_id;
  console.log(label_name)
  console.log(image_label_id)
  fetch(address + "/labels/update", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      "label_name": label_name,
      "image_label_id": image_label_id
    })
  })
  .then(async response => {
    const data = await response.json()
    if (data.error) {
      req.flash("error", data.message);
    } else {
      req.flash("success", data.message);
    }
    return res.redirect('/');
  })
})

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})