/* ReMake — upload UI + call to the AI backend. */
(function () {
	"use strict";

	var MAX_FILES = 4;
	var MAX_BYTES = 8 * 1024 * 1024; // 8 MB

	var fileInput = document.getElementById("file-input");
	var dropzone = document.getElementById("dropzone");
	var thumbs = document.getElementById("thumbs");
	var note = document.getElementById("note");
	var form = document.getElementById("scan-form");
	var generateBtn = document.getElementById("generate-btn");

	var result = document.getElementById("result");
	var resultStatus = document.getElementById("result-status");
	var statusText = document.getElementById("status-text");
	var resultBody = document.getElementById("result-body");
	var resultError = document.getElementById("result-error");
	var howBlock = document.querySelector("[data-howblock]");

	// Keep our own list of selected files (input.files is read-only).
	var files = [];

	function syncButton() {
		generateBtn.disabled = files.length === 0;
	}

	function renderThumbs() {
		thumbs.innerHTML = "";
		files.forEach(function (file, i) {
			var wrap = document.createElement("div");
			wrap.className = "thumb";
			var img = document.createElement("img");
			img.alt = file.name;
			img.src = URL.createObjectURL(file);
			img.onload = function () { URL.revokeObjectURL(img.src); };
			var btn = document.createElement("button");
			btn.type = "button";
			btn.setAttribute("aria-label", "Remove image");
			btn.textContent = "×";
			btn.onclick = function () {
				files.splice(i, 1);
				renderThumbs();
				syncButton();
			};
			wrap.appendChild(img);
			wrap.appendChild(btn);
			thumbs.appendChild(wrap);
		});
	}

	function addFiles(list) {
		var incoming = Array.prototype.slice.call(list);
		for (var i = 0; i < incoming.length; i++) {
			var f = incoming[i];
			if (!f.type || f.type.indexOf("image/") !== 0) continue;
			if (f.size > MAX_BYTES) {
				alert('"' + f.name + '" is larger than 8 MB and was skipped.');
				continue;
			}
			if (files.length >= MAX_FILES) {
				alert("You can add up to " + MAX_FILES + " photos.");
				break;
			}
			files.push(f);
		}
		renderThumbs();
		syncButton();
	}

	// Click / keyboard on the dropzone opens the file picker.
	dropzone.addEventListener("click", function () { fileInput.click(); });
	dropzone.addEventListener("keydown", function (e) {
		if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); }
	});
	fileInput.addEventListener("change", function () { addFiles(fileInput.files); fileInput.value = ""; });

	// Drag & drop.
	["dragenter", "dragover"].forEach(function (ev) {
		dropzone.addEventListener(ev, function (e) { e.preventDefault(); dropzone.classList.add("dragover"); });
	});
	["dragleave", "drop"].forEach(function (ev) {
		dropzone.addEventListener(ev, function (e) { e.preventDefault(); dropzone.classList.remove("dragover"); });
	});
	dropzone.addEventListener("drop", function (e) {
		if (e.dataTransfer && e.dataTransfer.files) addFiles(e.dataTransfer.files);
	});

	function showResultShell() {
		result.classList.add("show");
		if (howBlock) howBlock.style.display = "none";
		resultError.style.display = "none";
		resultBody.style.display = "none";
		resultStatus.style.display = "flex";
		result.scrollIntoView({ behavior: "smooth", block: "start" });
	}

	function showError(message) {
		resultStatus.style.display = "none";
		resultBody.style.display = "none";
		resultError.style.display = "block";
		resultError.textContent = message;
	}

	var STATUS_STEPS = [
		"Reading your material…",
		"Identifying what it could become…",
		"Designing your product…",
		"Rendering the finished piece…"
	];

	function cycleStatus() {
		var i = 0;
		statusText.textContent = STATUS_STEPS[0];
		return setInterval(function () {
			i = (i + 1) % STATUS_STEPS.length;
			statusText.textContent = STATUS_STEPS[i];
		}, 2500);
	}

	function renderResult(data) {
		resultStatus.style.display = "none";
		resultError.style.display = "none";

		document.getElementById("result-material").textContent = data.material || "Upcycled material";
		document.getElementById("result-name").textContent = data.product_name || "Your new product";
		document.getElementById("result-desc").textContent = data.description || "";

		var img = document.getElementById("result-image");
		if (data.image) {
			img.src = data.image;
			img.parentElement.style.display = "";
		} else {
			img.parentElement.style.display = "none";
		}

		var meta = document.getElementById("result-meta");
		meta.innerHTML = "";
		function chip(label, value) {
			if (!value) return;
			var el = document.createElement("span");
			el.className = "chip";
			el.textContent = label + ": " + value;
			meta.appendChild(el);
		}
		chip("Effort", data.effort);
		chip("Time", data.time);
		if (Array.isArray(data.tools)) {
			data.tools.forEach(function (t) { chip("Tool", t); });
		}
		if (data.impact) chip("Impact", data.impact);

		var steps = document.getElementById("result-steps");
		steps.innerHTML = "";
		(data.steps || []).forEach(function (s) {
			var li = document.createElement("li");
			li.textContent = s;
			steps.appendChild(li);
		});

		resultBody.style.display = "block";
	}

	form.addEventListener("submit", function (e) {
		e.preventDefault();
		if (files.length === 0) return;

		generateBtn.disabled = true;
		showResultShell();
		var statusTimer = cycleStatus();

		var fd = new FormData();
		files.forEach(function (f) { fd.append("images", f, f.name); });
		fd.append("note", note.value || "");

		fetch("/api/generate", { method: "POST", body: fd })
			.then(function (res) {
				return res.json().then(function (body) { return { ok: res.ok, body: body }; });
			})
			.then(function (r) {
				clearInterval(statusTimer);
				if (!r.ok || r.body.error) {
					showError(r.body.error || "Something went wrong generating your product. Please try again.");
				} else {
					renderResult(r.body);
				}
			})
			.catch(function () {
				clearInterval(statusTimer);
				showError("Could not reach the server. Check your connection and try again.");
			})
			.finally(function () {
				generateBtn.disabled = files.length === 0;
			});
	});

	syncButton();
})();
