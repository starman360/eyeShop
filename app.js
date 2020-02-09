var express = require("express");
var stylus = require("stylus");
var nib = require("nib");
var app = express();
var https = require("https");
var http = require("http").createServer(app);
var io = require("socket.io")(http);


var apikey =
  "?api-version=2018-10-18&subscription-key=9809b763453f4e989d5082a9ec49b65e";

var port = 3000;

var sockets = {};

function compile(str, path) {
  return stylus(str)
    .set("filename", path)
    .use(nib());
}

function goGET(endpoint, callback) {
  console.log(endpoint);
  https
    .get(endpoint, resp => {
      let data = "";

      // A chunk of data has been recieved.
      resp.on("data", chunk => {
        data += chunk;
      });

      // The whole response has been received. Print out the result.
      resp.on("end", () => {
        console.log("NOW");
        callback(JSON.parse(data));
      });
    })
    .on("error", err => {
      console.log("Error: " + err.message);
    });
}

function queryWegmansB(barcode) {
  return new Promise((resolve, reject) => {
    goGET(
      "https://api.wegmans.io/products/barcodes/" + barcode + apikey,
      resolve
    );
    setTimeout(function() {
      reject("It Broke");
    }, 10000);
  });
}

function queryWegmansP(sku) {
  return new Promise((resolve, reject) => {
    goGET("https://api.wegmans.io/products/" + sku + apikey, resolve);
    setTimeout(function() {
      reject("It Broke");
    }, 10000);
  });
}

app.set("views", __dirname + "/views");
app.set("view engine", "pug");
app.use(stylus.middleware({ src: __dirname + "/public", compile: compile }));
app.use(express.static(__dirname + "/public"));
// app.use("/stylesheets", express.static(__dirname + "/node_modules/bootstrap/dist/css"));
// app.use("/js", express.static(__dirname + "/node_modules/bootstrap/dist/js"));
app.use("/js", express.static(__dirname + "/public/js"));
app.use("/jquery", express.static(__dirname + "/node_modules/jquery/dist"));
app.use("/qr", express.static(__dirname + "/node_modules/qrcode/build"));

app.use(
  "/socket.io",
  express.static(__dirname + "/node_modules/socket.io-client/dist")
);
app.use(
  "/popperjs",
  express.static(__dirname + "/node_modules/@popperjs/core/dist/umd")
);

app.get("/", function(req, res) {
  res.render("index", { title: "Home" });
});

app.get("/checkout", function(req, res) {
	if (req.query.data !== undefined){
		console.log(req.query.data);
		var data = req.query.data.split(',').splice(-1,1)
	}
	res.render("checkout", { title: "checkout", dta: data});
});

io.on("connection", function(socket) {
  var id = 0;
  socket.on("socketID", id => {
    console.log("A User connected with Id: " + id);
    sockets[id] = socket;
  });
  socket.on("sync", data => {
    console.log(data.key);
    console.log(data.payload);
    if (sockets[data.key] !== undefined) {
      soc = sockets[data.key];
      soc.emit("pupilconn", 1);
    }
  });
  socket.on("barcode", data => {
    console.log(data.key);
    console.log(data.payload);
    if (sockets[data.key] !== undefined) {
      Promise.resolve(queryWegmansB(data.payload))
        .then(sku => {
          if (sku["error"] !== undefined) {
            soc.emit("food", "oops");
          } else {
            Promise.resolve(queryWegmansP(sku.sku))
              .then(prod => {
                // IM GETTING DATA HERE
                console.log(prod);
                soc = sockets[data.key];
                soc.emit("food", JSON.stringify(prod));
              })
              .catch(msg => {
                soc.emit("food", "oops");
              });
          }
        })
        .catch(msg => {
          soc.emit("food", "oops");
        });
      // console.log(sku);
      // sku = JSON.parse(sku).sku
      // prod = queryWegmansP(sku);
      // console.log(prod);
    }
  });
});

http.listen(3000, function() {
  console.log("listening on *:3000");
});
