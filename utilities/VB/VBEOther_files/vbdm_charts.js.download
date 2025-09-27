function digimonDetailsAJAX(digimon) {
    var reveal = digimon;
	if (reveal != "blank" && reveal != "rest") {
		var digimonreveal = "#" + reveal + "_card";
        var card = document.createElement("div");
        if (document.getElementById(reveal + "_card") == null) {
            card.setAttribute("id", reveal + "_card");
            card.setAttribute("class", "detailsExt");
            document.body.appendChild(card);
            var xmlhttp = new XMLHttpRequest();
            xmlhttp.onreadystatechange = function() {
    		  if (this.readyState == 4 && this.status == 200) {
          		  document.getElementById(reveal + "_card").innerHTML = this.responseText;
			  }
            };
            xmlhttp.open("GET","//humulos.com/digimon/vbdm/php/details_ajax.php?digimon="+digimon,true);
            xmlhttp.send();
        };
		document.addEventListener("click", handler, true);
		function handler(e) {
			e.stopPropagation();
			e.preventDefault();
		  };
		setTimeout(function() {
			$(digimonreveal).show(500);
		}, 250);
		$(".close").show(0);
		$("#victories").show(0);
		$("#shade").show(500);
		$("#faq_circle").hide(0);
		$("#discord_circle").hide(0);
		$("#legendtoggle").hide(0);
		$("#arttoggle").hide(0);
		$("body").css("overflow", "hidden");
		$("body").css("margin-right", "17px");
		$("#menu").css("width", "calc(100% - 17px)");
		window.history.pushState(reveal, reveal);
		setTimeout(function() {
			document.removeEventListener("click", handler, true);
		}, 500);
	};
};
function digimonShinkaAJAX(targetMon, current, copy) {
	shinkatarget = "#" + targetMon + "_card";
	shinkacurrent = "#" + current + "_card";
    digimon = window[targetMon];
    var reveal = targetMon;
	if (reveal != "blank" && reveal != "rest") {
		var digimonreveal = "#" + reveal + "_card";
        var card = document.createElement("div");
        if (document.getElementById(reveal + "_card") == null) {
            card.setAttribute("id", reveal + "_card");
            card.setAttribute("class", "detailsExt");
            document.body.appendChild(card);
            var xmlhttp = new XMLHttpRequest();
            xmlhttp.onreadystatechange = function() {
    		  if (this.readyState == 4 && this.status == 200) {
          		  document.getElementById(reveal + "_card").innerHTML = this.responseText;
			  }
            };
            xmlhttp.open("GET","//humulos.com/digimon/vbdm/php/details_ajax.php?digimon="+reveal,true);
            xmlhttp.send();
        };
		document.addEventListener("click", handler, true);
		function handler(e) {
			e.stopPropagation();
			e.preventDefault();
		  };
		setTimeout(function() {
			$(digimonreveal).show(500);
		}, 250);
		var isCopy = String(copy);
		var currentstring = String(targetMon);
		if (currentstring.indexOf("digitama") >= 0) {
		} else if (isCopy.indexOf("Enter") >= 0) {
		} else if (currentstring == "blank") {
		} else if (currentstring == "rest") {
		} else {
			$(shinkacurrent).hide(500);
		};
		setTimeout(function() {
			document.removeEventListener("click", handler, true);
		}, 500);
	};
};
function verticalsHeight(family, branch) {
	var lastLine = $("#" + family + "_" + branch + "_last");
	var firstLine = $("#" + family + "_" + branch + "_first");
	var theTop = $("#" + family).offset().top;
	var lastLineTop = Math.round(lastLine.offset().top);
	var firstLineTop = Math.round(firstLine.offset().top);
	var verticals = lastLineTop - firstLineTop + 5;
	var distance = firstLineTop - theTop;
	document.getElementById(family + "_" + branch + "_conn").style.height =
		verticals + "px";
	document.getElementById(family + "_" + branch + "_conn").style.top =
		distance + "px";
}
function verticalsHeightC(family, branch) {
	var lastLine = $('#' + family + '_' + branch + '_last');
	var firstLine = $('#' + family + '_' + branch + '_first');
	var theTop = $('#' + family).offset().top;
	var verticals = Math.floor((lastLine.offset().top - firstLine.offset().top) + 5);
	var distance = 25.5;
	document.getElementById(family + '_' + branch + '_conn').style.height = verticals + 'px';
	/*document.getElementById(family + '_' + branch + '_conn').style.top = (distance) + 'px';*/
};
function verticalsHeightCA(family, branch) {
	var lastLine = $('#' + family + '_' + branch + '_last');
	var firstLine = $('#' + family + '_' + branch + '_first');
	var theTop = $('#' + family).offset().top;
	var verticals = Math.floor((lastLine.offset().top - firstLine.offset().top) + 5);
	var distance = 34.5;
	document.getElementById(family + '_' + branch + '_conn').style.height = verticals + 'px';
	document.getElementById(family + '_' + branch + '_conn').style.top = (distance) + 'px';
};
function checkFilter(toggleBy, toggleValue, toggler) {
	if (document.getElementById(toggleBy + '_' + toggleValue).checked == true) {
		$('tr[' + toggleBy + '=' + toggleValue + ']').show(250);
		if (toggleBy = 'stage') {
			if (document.getElementById('attribute_Vaccine').checked == false) {
				$('tr[attribute="Vaccine"]').hide(250);
			};
			if (document.getElementById('attribute_Data').checked == false) {
				$('tr[attribute="Data"]').hide(250);
			};
			if (document.getElementById('attribute_Virus').checked == false) {
				$('tr[attribute="Virus"]').hide(250);
			};
			if (document.getElementById('attribute_Free').checked == false) {
				$('tr[attribute="Free"]').hide(250);
			};
			if (document.getElementById('activity_Stoic').checked == false) {
				$('tr[activity="Stoic"]').hide(250);
			};
			if (document.getElementById('activity_Active').checked == false) {
				$('tr[activity="Active"]').hide(250);
			};
			if (document.getElementById('activity_Normal').checked == false) {
				$('tr[activity="Normal"]').hide(250);
			};
			if (document.getElementById('activity_Indoor').checked == false) {
				$('tr[activity="Indoor"]').hide(250);
			};
			if (document.getElementById('activity_Lazy').checked == false) {
				$('tr[activity="Lazy"]').hide(250);
			};
		};
		if (toggleBy = 'attribute') {
			if (document.getElementById('stage_I').checked == false) {
				$('tr[stage="I"]').hide(250);
			};
			if (document.getElementById('stage_II').checked == false) {
				$('tr[stage="II"]').hide(250);
			};
			if (document.getElementById('stage_III').checked == false) {
				$('tr[stage="III"]').hide(250);
			};
			if (document.getElementById('stage_IV').checked == false) {
				$('tr[stage="IV"]').hide(250);
			};
			if (document.getElementById('stage_V').checked == false) {
				$('tr[stage="V"]').hide(250);
			};
			if (document.getElementById('stage_VI').checked == false) {
				$('tr[stage="VI"]').hide(250);
			};
			if (document.getElementById('activity_Stoic').checked == false) {
				$('tr[activity="Stoic"]').hide(250);
			};
			if (document.getElementById('activity_Active').checked == false) {
				$('tr[activity="Active"]').hide(250);
			};
			if (document.getElementById('activity_Normal').checked == false) {
				$('tr[activity="Normal"]').hide(250);
			};
			if (document.getElementById('activity_Indoor').checked == false) {
				$('tr[activity="Indoor"]').hide(250);
			};
			if (document.getElementById('activity_Lazy').checked == false) {
				$('tr[activity="Lazy"]').hide(250);
			};
		};
		if (toggleBy = 'activity') {
			if (document.getElementById('stage_I').checked == false) {
				$('tr[stage="I"]').hide(250);
			};
			if (document.getElementById('stage_II').checked == false) {
				$('tr[stage="II"]').hide(250);
			};
			if (document.getElementById('stage_III').checked == false) {
				$('tr[stage="III"]').hide(250);
			};
			if (document.getElementById('stage_IV').checked == false) {
				$('tr[stage="IV"]').hide(250);
			};
			if (document.getElementById('stage_V').checked == false) {
				$('tr[stage="V"]').hide(250);
			};
			if (document.getElementById('stage_VI').checked == false) {
				$('tr[stage="VI"]').hide(250);
			};
			if (document.getElementById('attribute_Vaccine').checked == false) {
				$('tr[attribute="Vaccine"]').hide(250);
			};
			if (document.getElementById('attribute_Data').checked == false) {
				$('tr[attribute="Data"]').hide(250);
			};
			if (document.getElementById('attribute_Virus').checked == false) {
				$('tr[attribute="Virus"]').hide(250);
			};
			if (document.getElementById('attribute_Free').checked == false) {
				$('tr[attribute="Free"]').hide(250);
			};
		};
	}
	else {
		$('tr[' + toggleBy + '=' + toggleValue + ']').hide(250);
	};
}
function clearFilter(toggleBy, button) {
		restoreText = button.innerHTML;
		button.innerHTML = 'Please wait...';
		setTimeout(function() {
			if (toggleBy == 'stage') {
				$('.stageCheck').prop('checked',false);
			};
			if (toggleBy == 'attribute') {
				$('.attributeCheck').prop('checked',false);
			};
			if (toggleBy == 'activity') {
				$('.activityCheck').prop('checked',false);
			};
			$('.digimon_row').hide(250);
			button.innerHTML = restoreText;
		},250);
	};
$(document).ready(function() {
	$('.chart').css('opacity','1');
	$('.extraroom80').css('padding-top', '80px');
	$('.extraroom100').css('padding-top', '100px');
	$('.extraroom120').css('padding-top', '120px');
	$('.extraroom140').css('padding-top', '140px');
});