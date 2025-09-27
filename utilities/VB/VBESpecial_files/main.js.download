//Shows toggle elements when width is wide enough
if ($(window).width() > 1150) {
	$("#row2").show(250);
	$("#row3").show(250);
	$("#row4").show(250);
}
//Hides toggle elements when width is too small
$(window).on("resize", function () {
	if ($(window).width() < 1151) {
		$("#row2").hide(250);
		$("#row3").hide(250);
		$("#row4").hide(250);
	}
});

//--------------------------------
// Settings Functions
//--------------------------------

function settingChange(setting, option) {
	// Controls what happens when one of the settings toggles is changed
	var currentSetting = (localStorage.getItem(setting) !== null ? localStorage.getItem(setting) : 0);
	if (currentSetting != option) {
		var option = option;
		if (option == 'invoke') {
			option = parseInt(currentSetting);
		} else {
			localStorage.setItem(setting, option);
		};
		switch (setting) {
			case "chartModeDesktop":
				chartless(option, 0);
				break;
			case "chartModeMobile":
				chartless(option, 1);
				break;
			case "spoilerDigimon":
				spoiler(option, '.digimon');
				break;
			case "spoilerRequirement":
				spoiler(option, 'div[class^="reqs"]');
				break;
			case "profileImage":
				profileImage(option);
				break;
			case "profileBackground":
				profileBackground(option);
				break;
			case "profileAnimation":
				profileAnimation(option);
				break;
		};
		var targetChoice = option + 1;
		$('#' + setting + ' .chosenSetting').removeClass("chosenSetting");
		$('#' + setting + ' .settingChoice:nth-child(' + targetChoice + ')').addClass("chosenSetting");
	};
};

function profileAnimation(choice) {
	// Actions for the Animations setting
	if (choice === 1) {
		$(".frame2Container").css("display", "none");
		$(".frame2").css("display", "none");
	}
	else {
		$(".frame2Container").css("display", "");
		$(".frame2").css("display", "");
	};
};

function profileBackground(choice) {
	// Actions for the Backgrounds setting
	if (choice === 1) {
		$(".spriteBG").css("background-size", "0");
		$(".spriteBG img").css("background", "#ffffff");
	}
	else {
		$(".spriteBG").css("background-size", "");
		$(".spriteBG img").css("background", "");
	};
};

function profileImage(choice) {
	// Actions for the Images setting
	$(".artswitch").each(function () {
		$(this).attr("src", $(this).attr("data-src"))
	});
	if (choice === 1) {
		$(".profile .dot").hide(0);
		$(".profile .art").show(0);
	}
	else {
		$(".profile .dot").show(0);
		$(".profile .art").hide(0);
	};
};

function spoiler(choice, target) {
	// Actions for the Digimon and Requirement Visibility settings
	if (choice === 1) {
		$(target).addClass("blackOut")
	} else {
		$(target).removeClass("blackOut")
	};
};

function chartless(choice, view) {
	// Actions for the Desktop and Mobile Chart Style settings
	if (
		window.location.href.indexOf("vbdm") > -1
		||
		window.location.href.indexOf("vbbe") > -1
		||
		window.location.href.indexOf("dmc") > -1
		||
		window.location.href.indexOf("penc") > -1
		||
		window.location.href.indexOf("dmh") > -1
		||
		window.location.href.indexOf("dmgz") > -1

	) {
		var state = choice;
		if (
			(
				(state === 1)
				&&
				(($(window).width() > 425 && view === 0))
			)
			||
			(
				(state === 0)
				&&
				($(window).width() <= 425 && view === 1)

			)
		) {
			$(".reqToggle").addClass("reqToggleMob");
			$(".chart").addClass("chartMob");
			$(".digitama").addClass("digitamaMob");
			$(".chart .column").addClass("columnMob");
			$(".chart .row").addClass("rowMob");
			$(".chart .digimon").addClass("digimonMob");
		} else if (
			(
				(state === 0)
				&&
				(($(window).width() > 425 && view === 0))
			)
			||
			(
				(state === 1)
				&&
				($(window).width() <= 425 && view === 1)

			)
		) {
			$(".reqToggle").removeClass("reqToggleMob");
			$(".chart").removeClass("chartMob");
			$(".digitama").removeClass("digitamaMob");
			$(".chart .column").removeClass("columnMob");
			$(".chart .row").removeClass("rowMob");
			$(".chart .digimon").removeClass("digimonMob");
		};
	};
};

//--------------------------------
// Checklist Functions
//--------------------------------

function checkBox(version, digimon, self) {
	// Actions for when a checkbox is toggled
	var boxChecked = $(self).prop('checked');
	if (boxChecked) {
		if (tracker.filter((versionFilter) => versionFilter[version]).length < 1) {
			versionObject = {};
			versionObject[version] = [digimon];
			tracker.push(versionObject);
		};
		if (tracker.filter((versionFilter) => versionFilter[version])[0][version].filter((digimonFilter) => digimonFilter == digimon).length < 1) {
			tracker.filter((versionFilter) => versionFilter[version])[0][version].push(digimon);
		};
	} else {
		var versionArray = tracker.filter((versionFilter) => versionFilter[version]);
		var versionObject = versionArray[0];
		var monArray = versionObject[version];
		var monRemove = monArray.indexOf(digimon);
		if (monRemove > -1) {
			monArray.splice(monRemove, 1);
		};
		if (monArray.length < 1) {
			versionRemove = tracker.findIndex((trackerIndex) => trackerIndex[version]);
			tracker.splice(versionRemove, 1);
		};
	};
	updateBackup();
	localStorage.setItem(savedKey, JSON.stringify(trackerObject));
};

function copyCode(copiedCode) {
	// Actions for when the Copy button is clicked
	var copyText = document.getElementById(copiedCode);
	copyText.select();
	document.execCommand("copy");
	document.getSelection().removeAllRanges();
};

function loadCode(loadedCode) {
	// Actions for when the Load button is clicked
	var loadText = $('#' + loadedCode).val();
	try {
		var loadObject = JSON.parse(loadText);
	} catch (err) {
		alert('I ain\'t loading that');
	};
	var loadObjectKey = Object.keys(loadObject)[0];
	var savedItemKey = Object.keys(trackerObject)[0];
	var structureCheck = (loadObject[loadObjectKey][0] !== undefined ? Object.values(loadObject[loadObjectKey][0])[0][0] : null);
	if (structureCheck !== '' && typeof structureCheck === 'string') {
		if (loadObjectKey === savedItemKey) {
			if (confirm('WARNING! This operation will overwrite the existing checklist for this device in its entirety. This cannot be reversed, press OK if you wish to proceed.') == true) {
				localStorage.setItem(savedKey, loadText);
				$('input:checked').prop('checked', false);
				loadObject[loadObjectKey].forEach(loadVer);
				trackerObject = loadObject;
				tracker = loadObject[trackerDevice];
				alert('Checklist successfully updated');
			} else {
				alert('Nothing was updated');
			}
		} else {
			alert('The provided backup is not for this checklist');
		};
	} else {
		alert('I ain\'t loading that');
	};
};

function loadVer(splitVer) {
	// Findas all versions for the loaded text
	version = Object.keys(splitVer);
	splitVer[version].forEach(loadDigi);
};

function loadDigi(splitDigi) {
	// Checks the box for each Digimon found in loadVer
	var checkID = version + '_' + splitDigi;
	$('#' + checkID).prop('checked', true);
};

function clearCode() {
	// Actions for when the Clear button is clicked
	if (confirm('This will clear the checklist entirely, all saved progress will be lost. Click OK if you are sure you wish to proceed.') == true) {
		$('input:checked').prop('checked', false);
		alert('Checklist successfully cleared');
		var clearTrackerObject = {};
		var clearTrackerDevice = 'device' + device;
		clearTrackerObject[clearTrackerDevice] = [];
		localStorage.setItem(savedKey, JSON.stringify(clearTrackerObject));
		$('#checklistBackup').val('');
	} else {
		alert('Nothing was updated');
	}
};

function updateBackup() {
	// Controls the value of the input field
	if (tracker.length > 0) {
		$('#checklistBackup').val(JSON.stringify(trackerObject));
	} else {
		$('#checklistBackup').val('');
	};
};

function digimonDetailsUnified(digimon, device, version) {
	var reveal = digimon;
	if (reveal != "blank" && reveal != "rest") {
		reveal = digimon + version;
		var digimonreveal = "#" + reveal + "_card";
		var card = document.createElement("div");
		if (document.getElementById(reveal + "_card") == null) {
			card.setAttribute("id", reveal + "_card");
			card.setAttribute("class", "detailExt");
			document.getElementById("detailsContainer").appendChild(card);
			var xmlhttp = new XMLHttpRequest();
			xmlhttp.onreadystatechange = function () {
				if (this.readyState == 4 && this.status == 200) {
					document.getElementById(reveal + "_card").innerHTML = this.responseText;
				}
			};
			xmlhttp.open("GET", "//humulos.com/digimon/php/details.php?digimon=" + digimon + "&device=" + device + "&version=" + version, true);
			xmlhttp.send();
		};
		document.addEventListener("click", handler, true);
		function handler(e) {
			e.stopPropagation();
			e.preventDefault();
		};
		/*setTimeout(function () {
			$(digimonreveal).velocity(
				{
					width:560
				},
				{	
					duration:1000,
					easing: "easeInSine"
				}
			);
			$(digimonreveal).velocity(
				{
					opacity:1,
					height:"100%"
				},
				{
					duration:1000,
					easing: "easeInSine"
				}
			);
		}, 250);*/
		$('.frame2').css({ "animation": "none", "opacity": "0" });
		$('.frame2Container').css({ "animation": "none", "opacity": "0" });
		setTimeout(function () {
			$(digimonreveal).show(500);
		}, 250);
		$(".close").show(0);
		$("#victories").show(0);
		$("#shade").css("opacity", "0");
		$("#shade").show(0);
		$("#shade").animate({ opacity: 0.5 }, 500);
		$("#faq_circle").hide(0);
		$("#discord_circle").hide(0);
		$("#legendtoggle").hide(0);
		$("#arttoggle").hide(0);
		$("body").css("overflow", "hidden");
		$("body").css("margin-right", "17px");
		$("#menu").css("width", "calc(100% - 17px)");
		window.history.pushState(reveal, reveal);
		setTimeout(function () {
			document.removeEventListener("click", handler, true);
		}, 750);
	};
};
function digimonShinkaUnified(targetMon, current, device, version) {
	shinkatarget = "#" + targetMon + version + "_card";
	shinkacurrent = "#" + current + version + "_card";
	digimon = window[targetMon];
	var reveal = targetMon;
	if (reveal != "blank" && reveal != "rest") {
		reveal = targetMon + version;
		var digimonreveal = "#" + reveal + "_card";
		var card = document.createElement("div");
		if (document.getElementById(reveal + "_card") == null) {
			card.setAttribute("id", reveal + "_card");
			card.setAttribute("class", "detailExt");
			document.getElementById("detailsContainer").appendChild(card);
			var xmlhttp = new XMLHttpRequest();
			xmlhttp.onreadystatechange = function () {
				if (this.readyState == 4 && this.status == 200) {
					document.getElementById(reveal + "_card").innerHTML = this.responseText;
				}
			};
			xmlhttp.open("GET", "//humulos.com/digimon/php/details.php?digimon=" + targetMon + "&device=" + device + "&version=" + version, true);
			xmlhttp.send();
		};
		document.addEventListener("click", handler, true);
		function handler(e) {
			e.stopPropagation();
			e.preventDefault();
		};
		setTimeout(function () {
			$(digimonreveal).show(500);
		}, 250);
		$(shinkacurrent).hide(500);
		/*
		var isCopy = String(copy);
		var currentstring = String(targetMon);
		if (currentstring.indexOf("digitama") >= 0) {
		} else if (isCopy.indexOf("Enter") >= 0) {
		} else if (currentstring == "blank") {
		} else if (currentstring == "rest") {
		} else {
		};*/
		setTimeout(function () {
			document.removeEventListener("click", handler, true);
		}, 500);
	};
};
function verticalsHeightUnified(incomingLine, incomingVer, connType, speed) {
	var lastLine = $("." + incomingLine + "_line:visible").last();
	var firstLine = $("." + incomingLine + "_line:visible").first();
	var outLine = $("." + incomingLine + "_lineOut:visible");
	var theTop = $("#" + incomingVer).offset().top;
	var lastLineTop = Math.round(lastLine.offset().top);
	var firstLineTop = Math.round(firstLine.offset().top);
	if (connType != 'reqConn') {
		var outLineTop = Math.round(outLine.offset().top);
		if (outLineTop < firstLineTop) {
			var verticals = lastLineTop - outLineTop + 5;
		}
		else if (outLineTop > lastLineTop) {
			var verticals = outLineTop - firstLineTop + 5;
		}
		else {
			var verticals = lastLineTop - firstLineTop + 5;
		};
		if (outLineTop < firstLineTop) {
			var distance = outLineTop - theTop;
		}
		else {
			var distance = firstLineTop - theTop;
		};
	}
	else {
		var columnTop = $("#" + incomingLine + "_column").offset().top;
		var verticals = lastLineTop - firstLineTop + 5;
		var distance = firstLineTop - columnTop;
	};
	var speed = 0 + speed;
	$('#' + incomingLine + "_conn").animate({ top: distance }, speed);
	//document.getElementById(incomingLine + "_conn").style.top =	distance + "px";
	$('#' + incomingLine + "_conn").animate({ height: verticals }, speed);
	//document.getElementById(incomingLine + "_conn").style.height = verticals + "px";
};
function areaUpdate(area, sp, re, win, list) {

};
//Closes currently open card and opens the clicked evolution
function digimonShinka(target, current, copy) {
	var shinkatarget = $("#" + target + "_card");
	var shinkacurrent = $("#" + current + "_card");
	var digimonArtreveal = $("#" + target + "_card .art");
	var newURL = digimonArtreveal.attr("data-src");
	digimonArtreveal.attr("src", newURL);
	var isCopy = String(copy);
	var currentstring = String(target);
	if (currentstring == 'digitama') {
		shinkatarget.show(250);
		shinkacurrent.hide(250);
	} else if (currentstring.indexOf("digitama") >= 0) {
	} else if (isCopy.indexOf("Enter") >= 0) {
	} else if (currentstring == "blank") {
	} else if (currentstring == "rest") {
	} else {
		shinkatarget.show(250);
		shinkacurrent.hide(250);
	}
}
//Opens Digimon detail card when that Digimon is clicked
function digimonDetails(reveal) {
	if (reveal != "blank" && reveal != "rest") {
		var digimonreveal = $("#" + reveal + "_card");
		var digimonArtreveal = $("#" + reveal + "_card .art");
		var newURL = digimonArtreveal.attr("data-src");
		digimonArtreveal.attr("src", newURL);
		digimonreveal.show(250);
		$(".close").show(0);
		$("#victories").show(0);
		$("#shade").show(0);
		$("#faq_circle").hide(0);
		$("#discord_circle").hide(0);
		$("#legendtoggle").hide(0);
		$("#arttoggle").hide(0);
		$("body").css("overflow", "hidden");
		$("body").css("margin-right", "17px");
		$("#menu").css("width", "calc(100% - 17px)");
		window.history.pushState(reveal, reveal);
	}
}
//Creates and opens Digimon detail card when that Digimon is clicked
function digimonDetailsPen20(digimon) {
	var reveal = result[digimon]['url'];
	if (reveal != "blank" && reveal != "rest") {
		var digimonreveal = "#" + reveal + "_card";
		var card = document.createElement("div");
		if (document.getElementById(reveal + "_card") == null) {
			card.setAttribute("id", reveal + "_card");
			card.setAttribute("class", "details " + result[digimon]['attribute']);
			document.body.appendChild(card);
			$(digimonreveal).html('<div class="tabler"> <div class="arts"><img class="art" src="//humulos.com/digimon/images/art/' + result[digimon]['url'] + '.jpg"></div> <div class="diginame"> <p class="sub">' + result[digimon]['name'] + '</p> <p class="dub">' + result[digimon]['dub'] + '</p> </div> <div class="baseinfo"> <div class="dots"><img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['url'] + '.gif"></div> <div>Stage ' + result[digimon]['level'] + ' (' + result[digimon]['evoStage'] + ')</div> <div>' + result[digimon]['attribute'] + (result[digimon]['alt_attribute'] != null ? result[digimon]['alt_attribute'] : '') + '</div> </div> <div class="evolution"> <div class="prevo"> <h2>Evolves From</h2>' + (result[digimon]['prevo1'] ? '<div class="evolutions" id="' + result[digimon]['prevo1'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo1'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo1'] + '.gif"> <h3 class="names">' + result[digimon]['prevo1_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo1_req'] + '</p>' : '') + (result[digimon]['prevo2'] ? '<div class="evolutions" id="' + result[digimon]['prevo2'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo2'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo2'] + '.gif"> <h3 class="names">' + result[digimon]['prevo2_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo2_req'] + '</p>' : '') + (result[digimon]['prevo3'] ? '<div class="evolutions" id="' + result[digimon]['prevo3'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo3'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo3'] + '.gif"> <h3 class="names">' + result[digimon]['prevo3_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo3_req'] + '</p>' : '') + (result[digimon]['prevo4'] ? '<div class="evolutions" id="' + result[digimon]['prevo4'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo4'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo4'] + '.gif"> <h3 class="names">' + result[digimon]['prevo4_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo4_req'] + '</p>' : '') + (result[digimon]['prevo5'] ? '<div class="evolutions" id="' + result[digimon]['prevo5'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo5'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo5'] + '.gif"> <h3 class="names">' + result[digimon]['prevo5_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo5_req'] + '</p>' : '') + (result[digimon]['prevo6'] ? '<div class="evolutions" id="' + result[digimon]['prevo6'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo6'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo6'] + '.gif"> <h3 class="names">' + result[digimon]['prevo6_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo6_req'] + '</p>' : '') + (result[digimon]['prevo7'] ? '<div class="evolutions" id="' + result[digimon]['prevo7'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo7'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo7'] + '.gif"> <h3 class="names">' + result[digimon]['prevo7_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo7_req'] + '</p>' : '') + '</div> <div class="evo"> <h2>Evolves To</h2>' + (result[digimon]['evo1'] ? '<div class="evolutions" id="' + result[digimon]['evo1'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo1'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo1'] + '.gif"> <h3 class="names">' + result[digimon]['evo1_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo1_req'] + '</p>' : '') + (result[digimon]['evo2'] ? '<div class="evolutions" id="' + result[digimon]['evo2'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo2'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo2'] + '.gif"> <h3 class="names">' + result[digimon]['evo2_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo2_req'] + '</p>' : '') + (result[digimon]['evo3'] ? '<div class="evolutions" id="' + result[digimon]['evo3'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo3'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo3'] + '.gif"> <h3 class="names">' + result[digimon]['evo3_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo3_req'] + '</p>' : '') + (result[digimon]['evo4'] ? '<div class="evolutions" id="' + result[digimon]['evo4'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo4'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo4'] + '.gif"> <h3 class="names">' + result[digimon]['evo4_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo4_req'] + '</p>' : '') + (result[digimon]['evo5'] ? '<div class="evolutions" id="' + result[digimon]['evo5'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo5'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo5'] + '.gif"> <h3 class="names">' + result[digimon]['evo5_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo5_req'] + '</p>' : '') + (result[digimon]['evo6'] ? '<div class="evolutions" id="' + result[digimon]['evo6'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo6'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo6'] + '.gif"> <h3 class="names">' + result[digimon]['evo6_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo6_req'] + '</p>' : '') + '</div> </div> <div class="bj"> <div>Battle: ' + result[digimon]['battle'] + '</div> <div>Jogress: ' + result[digimon]['jogress'] + '</div> <div>Power: ' + result[digimon]['strength_value'] + '</div> </div> <div class="bj"> <div>Mega Hit (Giga Hit): ' + result[digimon]['shakes'] + '</div> <div>Sleep Time: ' + result[digimon]['sleep'] + '</div></div><div class="bj"><div>' + result[digimon]['note'] + '</div></div></div>');
		};
		$(digimonreveal).show(250);
		$(".close").show(0);
		$("#victories").show(0);
		$("#shade").show(0);
		$("#faq_circle").hide(0);
		$("#discord_circle").hide(0);
		$("#legendtoggle").hide(0);
		$("#arttoggle").hide(0);
		$("body").css("overflow", "hidden");
		$("body").css("margin-right", "17px");
		$("#menu").css("width", "calc(100% - 17px)");
		window.history.pushState(reveal, reveal);
	};
};
//Closes currently open card and opens the clicked evolution
function digimonShinkaPen20(targetMon, current, copy) {
	shinkatarget = "#" + targetMon + "_card";
	shinkacurrent = "#" + current + "_card";
	digimon = window[targetMon];
	var card = document.createElement("div");
	if (document.getElementById(targetMon + "_card") == null) {
		card.setAttribute("id", targetMon + "_card");
		card.setAttribute("class", "details " + result[digimon]['attribute']);
		document.body.appendChild(card);
		$(shinkatarget).html('<div class="tabler"> <div class="arts"><img class="art" src="//humulos.com/digimon/images/art/' + result[digimon]['url'] + '.jpg"></div> <div class="diginame"> <p class="sub">' + result[digimon]['name'] + '</p> <p class="dub">' + result[digimon]['dub'] + '</p> </div> <div class="baseinfo"> <div class="dots"><img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['url'] + '.gif"></div> <div>Stage ' + result[digimon]['level'] + ' (' + result[digimon]['evoStage'] + ')</div> <div>' + result[digimon]['attribute'] + (result[digimon]['alt_attribute'] != null ? result[digimon]['alt_attribute'] : '') + '</div> </div> <div class="evolution"> <div class="prevo"> <h2>Evolves From</h2>' + (result[digimon]['prevo1'] ? '<div class="evolutions" id="' + result[digimon]['prevo1'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo1'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo1'] + '.gif"> <h3 class="names">' + result[digimon]['prevo1_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo1_req'] + '</p>' : '') + (result[digimon]['prevo2'] ? '<div class="evolutions" id="' + result[digimon]['prevo2'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo2'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo2'] + '.gif"> <h3 class="names">' + result[digimon]['prevo2_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo2_req'] + '</p>' : '') + (result[digimon]['prevo3'] ? '<div class="evolutions" id="' + result[digimon]['prevo3'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo3'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo3'] + '.gif"> <h3 class="names">' + result[digimon]['prevo3_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo3_req'] + '</p>' : '') + (result[digimon]['prevo4'] ? '<div class="evolutions" id="' + result[digimon]['prevo4'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo4'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo4'] + '.gif"> <h3 class="names">' + result[digimon]['prevo4_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo4_req'] + '</p>' : '') + (result[digimon]['prevo5'] ? '<div class="evolutions" id="' + result[digimon]['prevo5'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo5'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo5'] + '.gif"> <h3 class="names">' + result[digimon]['prevo5_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo5_req'] + '</p>' : '') + (result[digimon]['prevo6'] ? '<div class="evolutions" id="' + result[digimon]['prevo6'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo6'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo6'] + '.gif"> <h3 class="names">' + result[digimon]['prevo6_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo6_req'] + '</p>' : '') + (result[digimon]['prevo7'] ? '<div class="evolutions" id="' + result[digimon]['prevo7'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['prevo7'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['prevo7'] + '.gif"> <h3 class="names">' + result[digimon]['prevo7_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo7_req'] + '</p>' : '') + '</div> <div class="evo"> <h2>Evolves To</h2>' + (result[digimon]['evo1'] ? '<div class="evolutions" id="' + result[digimon]['evo1'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo1'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo1'] + '.gif"> <h3 class="names">' + result[digimon]['evo1_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo1_req'] + '</p>' : '') + (result[digimon]['evo2'] ? '<div class="evolutions" id="' + result[digimon]['evo2'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo2'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo2'] + '.gif"> <h3 class="names">' + result[digimon]['evo2_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo2_req'] + '</p>' : '') + (result[digimon]['evo3'] ? '<div class="evolutions" id="' + result[digimon]['evo3'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo3'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo3'] + '.gif"> <h3 class="names">' + result[digimon]['evo3_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo3_req'] + '</p>' : '') + (result[digimon]['evo4'] ? '<div class="evolutions" id="' + result[digimon]['evo4'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo4'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo4'] + '.gif"> <h3 class="names">' + result[digimon]['evo4_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo4_req'] + '</p>' : '') + (result[digimon]['evo5'] ? '<div class="evolutions" id="' + result[digimon]['evo5'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo5'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo5'] + '.gif"> <h3 class="names">' + result[digimon]['evo5_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo5_req'] + '</p>' : '') + (result[digimon]['evo6'] ? '<div class="evolutions" id="' + result[digimon]['evo6'] + '_clicker" onClick="digimonShinkaPen20(\'' + result[digimon]['evo6'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/pen20/' + result[digimon]['evo6'] + '.gif"> <h3 class="names">' + result[digimon]['evo6_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo6_req'] + '</p>' : '') + '</div> </div> <div class="bj"> <div>Battle: ' + result[digimon]['battle'] + '</div> <div>Jogress: ' + result[digimon]['jogress'] + '</div> <div>Power: ' + result[digimon]['strength_value'] + '</div> </div> <div class="bj"> <div>Mega Hit (Giga Hit): ' + result[digimon]['shakes'] + '</div> <div>Sleep Time: ' + result[digimon]['sleep'] + '</div></div><div class="bj"><div>' + result[digimon]['note'] + '</div></div></div>');
	};
	var isCopy = String(copy);
	var currentstring = String(targetMon);
	if (currentstring.indexOf("digitama") >= 0) {
	} else if (isCopy.indexOf("Enter") >= 0) {
	} else if (currentstring == "blank") {
	} else if (currentstring == "rest") {
	} else {
		$(shinkatarget).show(250);
		$(shinkacurrent).hide(250);
	}
}//Creates and opens Digimon detail card when that Digimon is clicked
function digimonDetailsDM20(digimon) {
	var reveal = result[digimon]['url'];
	if (reveal != "blank" && reveal != "rest") {
		var digimonreveal = "#" + reveal + "_card";
		var card = document.createElement("div");
		if (document.getElementById(reveal + "_card") == null) {
			card.setAttribute("id", reveal + "_card");
			card.setAttribute("class", "details " + result[digimon]['attribute']);
			document.body.appendChild(card);
			$(digimonreveal).html('<div class="tabler"> <div class="arts"><img class="art" src="//humulos.com/digimon/images/art/' + result[digimon]['url'] + '.jpg"></div> <div class="diginame"> <p class="sub">' + result[digimon]['name'] + '</p> <p class="dub">' + result[digimon]['dub'] + '</p> </div> <div class="baseinfo"> <div class="dots"><img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['url'] + '.gif"></div> <div>Stage ' + result[digimon]['level'] + ' (' + result[digimon]['evoStage'] + ')</div> <div>' + result[digimon]['attribute'] + '</div> </div> <div class="evolution"> <div class="prevo"> <h2>Evolves From</h2>' + (result[digimon]['prevo1'] ? '<div class="evolutions" id="' + result[digimon]['prevo1'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo1'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo1'] + '.gif"> <h3 class="names">' + result[digimon]['prevo1_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo1_req'] + '</p>' : '') + (result[digimon]['prevo2'] ? '<div class="evolutions" id="' + result[digimon]['prevo2'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo2'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo2'] + '.gif"> <h3 class="names">' + result[digimon]['prevo2_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo2_req'] + '</p>' : '') + (result[digimon]['prevo3'] ? '<div class="evolutions" id="' + result[digimon]['prevo3'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo3'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo3'] + '.gif"> <h3 class="names">' + result[digimon]['prevo3_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo3_req'] + '</p>' : '') + (result[digimon]['prevo4'] ? '<div class="evolutions" id="' + result[digimon]['prevo4'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo4'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo4'] + '.gif"> <h3 class="names">' + result[digimon]['prevo4_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo4_req'] + '</p>' : '') + (result[digimon]['prevo5'] ? '<div class="evolutions" id="' + result[digimon]['prevo5'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo5'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo5'] + '.gif"> <h3 class="names">' + result[digimon]['prevo5_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo5_req'] + '</p>' : '') + (result[digimon]['prevo6'] ? '<div class="evolutions" id="' + result[digimon]['prevo6'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo6'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo6'] + '.gif"> <h3 class="names">' + result[digimon]['prevo6_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo6_req'] + '</p>' : '') + (result[digimon]['prevo7'] ? '<div class="evolutions" id="' + result[digimon]['prevo7'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo7'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo7'] + '.gif"> <h3 class="names">' + result[digimon]['prevo7_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo7_req'] + '</p>' : '') + '</div> <div class="evo"> <h2>Evolves To</h2>' + (result[digimon]['evo1'] ? '<div class="evolutions" id="' + result[digimon]['evo1'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo1'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo1'] + '.gif"> <h3 class="names">' + result[digimon]['evo1_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo1_req'] + '</p>' : '') + (result[digimon]['evo2'] ? '<div class="evolutions" id="' + result[digimon]['evo2'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo2'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo2'] + '.gif"> <h3 class="names">' + result[digimon]['evo2_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo2_req'] + '</p>' : '') + (result[digimon]['evo3'] ? '<div class="evolutions" id="' + result[digimon]['evo3'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo3'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo3'] + '.gif"> <h3 class="names">' + result[digimon]['evo3_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo3_req'] + '</p>' : '') + (result[digimon]['evo4'] ? '<div class="evolutions" id="' + result[digimon]['evo4'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo4'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo4'] + '.gif"> <h3 class="names">' + result[digimon]['evo4_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo4_req'] + '</p>' : '') + (result[digimon]['evo5'] ? '<div class="evolutions" id="' + result[digimon]['evo5'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo5'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo5'] + '.gif"> <h3 class="names">' + result[digimon]['evo5_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo5_req'] + '</p>' : '') + (result[digimon]['evo6'] ? '<div class="evolutions" id="' + result[digimon]['evo6'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo6'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo6'] + '.gif"> <h3 class="names">' + result[digimon]['evo6_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo6_req'] + '</p>' : '') + '</div> </div> <div class="bj"> <div>Power: ' + result[digimon]['strength_value'] + '</div> <div>Sleep Time: ' + result[digimon]['sleep'] + '</div></div></div>');
		};
		$(digimonreveal).show(250);
		$(".close").show(0);
		$("#victories").show(0);
		$("#shade").show(0);
		$("#faq_circle").hide(0);
		$("#discord_circle").hide(0);
		$("#legendtoggle").hide(0);
		$("#arttoggle").hide(0);
		$("body").css("overflow", "hidden");
		$("body").css("margin-right", "17px");
		$("#menu").css("width", "calc(100% - 17px)");
		window.history.pushState(reveal, reveal);
	};
};
//Closes currently open card and opens the clicked evolution
function digimonShinkaDM20(targetMon, current, copy) {
	shinkatarget = "#" + targetMon + "_card";
	shinkacurrent = "#" + current + "_card";
	digimon = window[targetMon];
	var card = document.createElement("div");
	if (document.getElementById(targetMon + "_card") == null) {
		card.setAttribute("id", targetMon + "_card");
		card.setAttribute("class", "details " + result[digimon]['attribute']);
		document.body.appendChild(card);
		$(shinkatarget).html('<div class="tabler"> <div class="arts"><img class="art" src="//humulos.com/digimon/images/art/' + result[digimon]['url'] + '.jpg"></div> <div class="diginame"> <p class="sub">' + result[digimon]['name'] + '</p> <p class="dub">' + result[digimon]['dub'] + '</p> </div> <div class="baseinfo"> <div class="dots"><img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['url'] + '.gif"></div> <div>Stage ' + result[digimon]['level'] + ' (' + result[digimon]['evoStage'] + ')</div> <div>' + result[digimon]['attribute'] + '</div> </div> <div class="evolution"> <div class="prevo"> <h2>Evolves From</h2>' + (result[digimon]['prevo1'] ? '<div class="evolutions" id="' + result[digimon]['prevo1'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo1'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo1'] + '.gif"> <h3 class="names">' + result[digimon]['prevo1_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo1_req'] + '</p>' : '') + (result[digimon]['prevo2'] ? '<div class="evolutions" id="' + result[digimon]['prevo2'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo2'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo2'] + '.gif"> <h3 class="names">' + result[digimon]['prevo2_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo2_req'] + '</p>' : '') + (result[digimon]['prevo3'] ? '<div class="evolutions" id="' + result[digimon]['prevo3'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo3'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo3'] + '.gif"> <h3 class="names">' + result[digimon]['prevo3_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo3_req'] + '</p>' : '') + (result[digimon]['prevo4'] ? '<div class="evolutions" id="' + result[digimon]['prevo4'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo4'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo4'] + '.gif"> <h3 class="names">' + result[digimon]['prevo4_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo4_req'] + '</p>' : '') + (result[digimon]['prevo5'] ? '<div class="evolutions" id="' + result[digimon]['prevo5'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo5'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo5'] + '.gif"> <h3 class="names">' + result[digimon]['prevo5_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo5_req'] + '</p>' : '') + (result[digimon]['prevo6'] ? '<div class="evolutions" id="' + result[digimon]['prevo6'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo6'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo6'] + '.gif"> <h3 class="names">' + result[digimon]['prevo6_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo6_req'] + '</p>' : '') + (result[digimon]['prevo7'] ? '<div class="evolutions" id="' + result[digimon]['prevo7'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['prevo7'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['prevo7'] + '.gif"> <h3 class="names">' + result[digimon]['prevo7_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['prevo7_req'] + '</p>' : '') + '</div> <div class="evo"> <h2>Evolves To</h2>' + (result[digimon]['evo1'] ? '<div class="evolutions" id="' + result[digimon]['evo1'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo1'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo1'] + '.gif"> <h3 class="names">' + result[digimon]['evo1_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo1_req'] + '</p>' : '') + (result[digimon]['evo2'] ? '<div class="evolutions" id="' + result[digimon]['evo2'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo2'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo2'] + '.gif"> <h3 class="names">' + result[digimon]['evo2_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo2_req'] + '</p>' : '') + (result[digimon]['evo3'] ? '<div class="evolutions" id="' + result[digimon]['evo3'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo3'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo3'] + '.gif"> <h3 class="names">' + result[digimon]['evo3_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo3_req'] + '</p>' : '') + (result[digimon]['evo4'] ? '<div class="evolutions" id="' + result[digimon]['evo4'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo4'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo4'] + '.gif"> <h3 class="names">' + result[digimon]['evo4_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo4_req'] + '</p>' : '') + (result[digimon]['evo5'] ? '<div class="evolutions" id="' + result[digimon]['evo5'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo5'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo5'] + '.gif"> <h3 class="names">' + result[digimon]['evo5_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo5_req'] + '</p>' : '') + (result[digimon]['evo6'] ? '<div class="evolutions" id="' + result[digimon]['evo6'] + '_clicker" onClick="digimonShinkaDM20(\'' + result[digimon]['evo6'] + '\',\'' + result[digimon]['url'] + '\')"> <img class="dot" src="//humulos.com/digimon/images/dot/dm20/' + result[digimon]['evo6'] + '.gif"> <h3 class="names">' + result[digimon]['evo6_name'] + '</h3>  </div> <p class="deets">' + result[digimon]['evo6_req'] + '</p>' : '') + '</div> </div> <div class="bj"> <div>Power: ' + result[digimon]['strength_value'] + '</div> <div>Sleep Time: ' + result[digimon]['sleep'] + '</div></div></div>');
	};
	var isCopy = String(copy);
	var currentstring = String(targetMon);
	if (currentstring.indexOf("digitama") >= 0) {
	} else if (isCopy.indexOf("Enter") >= 0) {
	} else if (currentstring == "blank") {
	} else if (currentstring == "rest") {
	} else {
		$(shinkatarget).show(250);
		$(shinkacurrent).hide(250);
	}
}
function menuExpand(target, series, initial, speed) {
	var speed = speed ?? 250;
	if (series == 'category') {
		console.log('Truth was found');
		var cateogoryArray = ['dm', 'pen', 'vital', 'digivice', 'xo'];
		if (initial == 1) {
			$('#menu_' + target + '_series_content').show(speed);
		} else {
			$('#menu_' + target + '_series_content').toggle(speed);
		};
		cateogoryArray.forEach(category => {
			if (category != target) {
				console.log('We looping');
				$('#menu_' + category + '_series_content').hide(speed);
			}
		});
	} else {
		var seriesObject = {
			dm: ['dm', 'dm20', 'dmx', 'dmc'],
			pen: ['pen', 'pen20', 'penz', 'penc'],
			vital: ['vbdm', 'vbbe'],
			digivice: ['dvc','d3c'],
			xo: ['dmh','dmgz']
		}
		if (initial == 1) {
			$('#menu_' + target + '_content').show(speed);
		} else {
			$('#menu_' + target + '_content').toggle(speed);
		};
		seriesObject[series].forEach(device => {
			if (device != target) {
				$('#menu_' + device + '_content').hide(speed);
			}
		});

	};
};
$(document).ready(function () {
	//Brings up the shade and close button when a row in the Digimon list is clicked
	$(".digimon_row").click(function () {
		$(this)
			.find("div")
			.show(250);
		$(".close").show(0);
		$("#shade").show(0);
		$("body").css("overflow", "hidden");
		$("body").css("margin-right", "17px");
		$("#menu").css("width", "calc(100% - 17px)");
	});
	//Closes cards, shade and close icon
	function closeAll() {
		$(".details").hide(250);
		$(".detailsNew").hide(250);
		$(".detailsExt").hide(250);
		$(".detailExt").hide(250);
		$(".close").hide(0);
		$("#shade").hide(0);
		$("#settingsMenu").hide(0);
		$("#hiddenshade").hide(250);
		$("#legend").hide(0);
		$("#faq").hide(0);
		$("#about").hide(0);
		$("#victories").hide(0);
		$("#faq_circle").show(0);
		$("#discord_circle").show(0);
		$("#legendtoggle").show(0);
		$("#arttoggle").show(0);
		$("body").css("overflow", "auto");
		$("body").css("margin-right", "0");
		$("#menu").css("width", "100%");
		$('.frame2').css("animation", "");
		$('.frame2Container').css("animation", "");
	};
	$(".close").click(function () {
		closeAll();
	});
	window.onpopstate = function () {
		closeAll();
	};
	$("#shade").click(function () {
		closeAll();
	});
	$("#arttoggle").click(function () {
		$("#arttoggle").hide(250);
		$(".artswitch").each(function () {
			$(this).attr("src", $(this).attr("data-src"))
		});
		setTimeout(function () {
			$(".artswitch").toggle(0);
			setTimeout(function () {
				$("#arttoggle").show(250);
			}, 250);
		}, 250);
	});
	//Opens hamburger menu
	$("#hamburger").click(function () {
		$("#hiddenshade").toggle(0);
		if ($(window).width() < 426) {
			$("#hamburgermenu").toggle(250);
			$("#row2").hide(250);
			$("#row3").hide(250);
			$("#row4").hide(250);
		} else {
			$("#hamburgermenu").toggle(0);
		};
		var currentDevice = window.location.href.split('/')[4];
		var deviceObject = {
			'dm':'dm',
			'dm20':'dm',
			'dmx':'dm',
			'dmc':'dm',
			'pen':'pen',
			'pen20':'pen',
			'penz':'pen',
			'penc':'pen',
			'vbdm':'vital',
			'vbbe':'vital',
			'dvc':'digivice',
			'd3c':'digivice',
			'dmh':'xo',
			'dmgz':'xo'
		};
		menuExpand(deviceObject[currentDevice],'category',1,0);
		menuExpand(currentDevice,deviceObject[currentDevice],1,0);
	});

	$("#settingsGear").click(function () {
		$("#shade").toggle(0);
		if ($(window).width() < 426) {
			$("#settingsMenu").toggle(250);
			$("#row2").hide(250);
			$("#row3").hide(250);
			$("#row4").hide(250);
		} else {
			$("#settingsMenu").toggle(250);
		};
	});
	//Hides hamburger menu
	$("#hiddenshade").click(function () {
		$("#hiddenshade").hide(0);
		$("#hamburgermenu").hide(0);
		$("#settingsMenu").hide(250);
		$(".menu_content").hide(0);
		$("#legend").hide(250);
	});

	$("#listtoggle").click(function () {
		$("#listtoggle").hide(250);
		setTimeout(function () {
			$("#digimon_list").removeClass("card_view");
			$(".padding").addClass("list_scrolling");
			setTimeout(function () {
				$("#cardtoggle").show(250);
			}, 250);
		}, 250);
	});
	$("#cardtoggle").click(function () {
		$("#cardtoggle").hide(250);
		setTimeout(function () {
			$("#digimon_list").addClass("card_view");
			$(".padding").removeClass("list_scrolling");
			setTimeout(function () {
				$("#listtoggle").show(250);
			}, 250);
		}, 250);
	});
	$("#about_link_mobile").click(function () {
		$("#about").show(250);
		$("#shade").show(0);
		$(".close").show(0);
		$("#hamburgermobile").hide(0);
		$("#row2").hide(0);
		$("#row3").hide(0);
		$("#row4").hide(0);
	});
	$("#about_link").click(function () {
		$("#menu_pen20_content").hide(250);
		$("#menu_dmx_content").hide(250);
		$("#menu_penz_content").hide(250);
		$("#about").show(250);
		$("#shade").show(0);
		$(".close").show(0);
		$("#hamburgermenu").hide(0);
		$("#hiddenshade").hide(0);
		$("body").css("overflow", "hidden");
		$("body").css("margin-right", "17px");
		$("#menu").css("width", "calc(100% - 17px)");
	});
});
$(document).ready(function () {
	settingChange('chartModeDesktop', 'invoke');
	settingChange('chartModeMobile', 'invoke');
	settingChange('spoilerDigimon', 'invoke');
	settingChange('spoilerRequirement', 'invoke');
	settingChange('profileImage', 'invoke');
	settingChange('profileBackground', 'invoke');
	settingChange('profileAnimation', 'invoke');
	$('*[class^="line"]').css('opacity', '1');
	$('.chart').css('opacity', '1');
	$("#mask").css("display", "none");
	$(".loader").css("display", "none");
	$("#versionmenu").click(function () {
		$("#row2").toggle(250);
		$("#row3").toggle(250);
		$("#row4").toggle(250);
		$("#rowHidden").toggle(250);
		$("#hamburgermenu").hide(250);
	});
});
