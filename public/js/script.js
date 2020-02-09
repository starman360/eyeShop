var w = $(document).width();
var isConnected = false;
var currentFoodData = "";
var shoppingcart = [];
var count = 0;
var currentSC = "";


socket.on("connect", () => {
  socket.emit("socketID", socket.id);
  console.log(socket.id);
  QRCode.toCanvas(
    document.getElementById("canvas"),
    "key#"+socket.id,
    { width: w * 0.5 },
    function(error) {
      if (error) console.error(error);
      console.log("success!");
    }
  );
});

socket.on("pupilconn", (state) => {
	isConnected = true;
	console.log(state);
	if (state){
		$("#canvas").hide();
		$("#foodinfo").show();
	}
});

socket.on("food", (data)=> {
	if (data == "oops"){
		foodItem = "<row><h1>Oops</h1><h4>Please Try Again... </h4></row>"
		$("#foodinfo").html(foodItem);
	}
	else {
		navigator.vibrate = navigator.vibrate || navigator.webkitVibrate || navigator.mozVibrate || navigator.msVibrate;
		if ("vibrate" in navigator) {
			navigator.vibrate(500);
		}
		data = JSON.parse(data);
		currentFoodData = data;
		foodItem = "<row><h1>" + data.name + "</h1><h4>Ingredients:</h4><p>" + data.ingredients + "</p></row><b>ALLERGIES: ";
		if (data.ingredients[0] !== undefined){
			if (data.ingredients[0].toLowerCase().includes("peanut")){
				foodItem += "PEANUTS, "
			}
			if (data.ingredients[0].toLowerCase().includes("wheat")){
				foodItem += "WHEAT, "
			}
			if (data.ingredients[0].toLowerCase().includes("soy")){
				foodItem += "SOY, "
			}
			if (data.ingredients[0].toLowerCase().includes("egg")){
				foodItem += "EGGS, "
			}
			if (data.ingredients[0].toLowerCase().includes("milk")){
				foodItem += "MILK, "
			}
		}
		foodItem += "</b><button class='btn btn-success btn btn-success' id='addtocart' type='button'>Add to Cart  <ion-icon name='cart' role='img' class='md hydrated' aria-label='cart'></ion-icon></button>";
		$("#foodinfo").html(foodItem);
		$("button#addtocart").on('click', function() {
			$("#cart ul").append('<li class="list-group-item"><span class="left">'+ currentFoodData.name +'</span><span class="right"><ion-icon id="cart' + count + '" name="close-circle" role="img" class="md hydrated" aria-label="close-circle"></ion-icon></span></li> ')
			console.log("Added: "+currentFoodData.name);
			shoppingcart.push(currentFoodData);
			$("#cart" + count).on('click', function(){
				id = $(this).attr('id');
				num = id[id.length-1];
				shoppingcart.splice(num, 1);
				console.log("removing " + num);
				$(this).parent().parent().remove();	
			});
			currentSC = ""
			for (const item in shoppingcart){
				currentSC += shoppingcart[item].sku + ",";
			}
			QRCode.toCanvas(
				document.getElementById("canvas2"),
				currentSC,
				{ width: w * 0.5 },
				function(error) {
				  if (error) console.error(error);
				  console.log("success!");
				}
			 );
			count = count +1;
		});
	}
});

$("button#addtocart").on('click', function() {
	$("#cart ul").append('<li class="list-group-item"><span class="left">'+ currentFoodData.name +'</span><span class="right"><ion-icon id="cart' + count + '" name="close-circle" role="img" class="md hydrated" aria-label="close-circle"></ion-icon></span></li> ')
	console.log("Added: "+currentFoodData.name);
	$("#cart" + count).on('click', function(){
		id = $(this).attr('id');
		num = id[id.length-1];
		shoppingcart.splice(num, 1);
		console.log("removing " + num);
		$(this).parent().parent().remove();	
	});
	count = count +1;
});



// $("button#addtocart").on('tap', function() {
// 	$("#cart ul").append('<li class="list-group-item">'+ currentFoodData.name +'</li> ')
// });

$("#homebtn").on("click", function() {
  $("#home").show();
  $("#cart").hide();
  $("#checkout").hide();
});
$("#cartbtn").on("click", function() {
  $("#home").hide();
  $("#cart").show();
  $("#checkout").hide();
});
$("#checkoutbtn").on("click", function() {
  $("#home").hide();
  $("#cart").hide();
  $("#checkout").show();
});
