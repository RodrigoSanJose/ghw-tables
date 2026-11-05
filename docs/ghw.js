/*
	Tables of generalized Hamming weights of projective Reed-Muller codes.

	This script only DISPLAYS the tables; they are computed by src/generate.py and stored in data/:
	  - data/index.json lists the tables (one for each pair q, m) and the references;
	  - data/q{q}_m{m}.json contains, for every code PRM_q(d,m), the lists lower, upper,
	    lower_reason and upper_reason, indexed by r (position 0 holds d_0 = 0).

	The address of the page says what is shown, for instance #q=3&m=3&d=4&r=7 (the table for q = 3,
	m = 3, with the entry d_7(PRM_3(4,3)) selected).  So every entry has its own link, and the
	links in the explanations are ordinary links.
*/

"use strict";

const COLUMNS = 10;            // row a and column b of a grid hold d_{a+b}, for b = 1, ..., 10
const EXPANDED_UP_TO = 60;     // codes with at most this many weights are shown expanded

let index = null;              // the contents of data/index.json
const downloaded = {};         // file name -> contents, for the tables already downloaded
let shown = null;              // {q, m, data}: the table currently shown
const expanded = {};           // "d" -> true or false, for the codes expanded or collapsed by hand


// ---------------------------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------------------------

function escapeHTML(text) {
	return String(text).replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
}

function math(tex) {                       // inline math, typeset by MathJax
	return '<span class="math">\\(' + tex + '\\)</span>';
}

function PRM(q, d, m) {
	return "\\mathrm{PRM}_{" + q + "}(" + d + "," + m + ")";
}

function RM(q, d, m) {
	return "\\mathrm{RM}_{" + q + "}(" + d + "," + m + ")";
}

function address(q, m, d, r) {             // the link to a table, or to one of its entries
	let hash = "#q=" + q + "&m=" + m;
	if (d !== undefined) hash += "&d=" + d;
	if (r !== undefined) hash += "&r=" + r;
	return hash;
}

function p(q, j) {                         // p_j = 1 + q + ... + q^j (0 if j < 0)
	let total = 0;
	for (let i = 0; i <= j; i++) total += q ** i;
	return total;
}

function binomial(a, b) {
	if (b < 0 || a < b) return 0;
	let result = 1;
	for (let i = 1; i <= b; i++) result = result * (a - b + i) / i;
	return Math.round(result);
}

function typeset(element) {
	// Ask MathJax to typeset new content.  If MathJax has not started yet, there is nothing to do:
	// when it starts, it typesets the whole page.  Otherwise we wait until it is ready.
	if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
		MathJax.startup.promise = MathJax.startup.promise
			.then(() => MathJax.typesetPromise([element]))
			.catch(error => console.log("MathJax: " + error.message));
	}
}

async function download(file) {
	if (!(file in downloaded)) {
		const response = await fetch("data/" + file);
		downloaded[file] = await response.json();
	}
	return downloaded[file];
}

function tableInfo(q, m) {                 // the entry of index.json for the table (q, m), if any
	return index.tables.find(t => t.q === q && t.m === m);
}

function codeOf(q, d, m) {                 // the data of the code PRM_q(d,m), if it is in the table shown
	if (!shown || shown.q !== q || shown.m !== m) return null;
	return shown.data.codes.find(c => c.d === d) || null;
}


// ---------------------------------------------------------------------------------------------
// The explanation of one bound
// ---------------------------------------------------------------------------------------------

// The text for d_alpha(PRM_q(dd, mm)) >= value, with a link to that entry when it is in the tables.
function inputWeight(q, dd, mm, alpha, value) {
	if (alpha === 0) return math("d_0 = 0");
	const name = "d_{" + alpha + "}(" + PRM(q, dd, mm) + ")";
	if (dd > mm * (q - 1) + 1) {           // the whole space, which is not listed in the tables
		return math(name + " = " + value) + " (the code is the whole space)";
	}
	return '<a href="' + address(q, mm, dd, alpha) + '">' + math(name + " \\ge " + value) + "</a>";
}

function explain(reason, q, d, m, r, value, k) {
	const n = p(q, m);
	switch (reason.rule) {

	case "PRM Thm 1.1": {
		const mu = reason.mu.join(",");
		return "Since " + math("d < q") + ", the weight is given by [PRM, Thm 1.1]: if "
			+ math("(\\mu_1,\\dots,\\mu_d)") + " is the Macaulay tuple of "
			+ math("\\binom{m+d}{d} - r = " + (binomial(m + d, d) - r)) + " in degree " + math("d")
			+ ", then " + math("d_r = p_m - p_{\\mu_d} - \\sum_{i=1}^{d-1} \\lfloor q^{\\mu_i} \\rfloor")
			+ ". Here " + math("(\\mu_1,\\dots,\\mu_" + d + ") = (" + mu + ")") + ".";
	}

	case "PRM Cor 4.2": {
		const e = reason.dual_degree;
		return "Since " + math("(m-1)(q-1) < d < m(q-1)") + ", the dual code is "
			+ '<a href="' + address(q, m, e) + '">' + math(PRM(q, e, m)) + "</a>"
			+ " [Sør91], whose weights are given by [PRM, Thm 1.1] because " + math(e + " < q")
			+ ". Wei duality [Wei91] then gives the whole hierarchy [PRM, Cor 4.2].";
	}

	case "whole space":
		return "Since " + math("d > m(q-1)") + ", the code is the whole space "
			+ math("\\mathbb{F}_{" + q + "}^{" + n + "}") + ", so " + math("d_r = r") + ".";

	case "dual is all-ones":
		return "Since " + math("d = m(q-1)") + ", the dual code is spanned by the all-ones vector [Sør91],"
			+ " and Wei duality [Wei91] gives " + math("d_r = r + 1") + ".";

	case "Sorensen":
		return "This is the minimum distance of " + math(PRM(q, d, m)) + ", computed by Sørensen [Sør91].";

	case "PRM Prop 6.12": {
		let text = "Given by [PRM, Prop 6.12], which determines the first weights when ";
		if ((d - 1) % (q - 1) === 0) {
			text += math("d = 1 + t(q-1)") + " (here " + math("t = " + (d - 1) / (q - 1)) + ").";
		} else {
			text += math("d = 2 + t(q-1)") + " and " + math("q \\ge 3") + " (here "
				+ math("t = " + (d - 2) / (q - 1)) + ").";
		}
		return text;
	}

	case "PRM Thm 6.7": {
		const points = reason.n;
		let text = "By [PRM, Thm 6.7], " + math("d_r \\le B_r(q,d,m) = p_m - n") + ", where " + math("n = " + points)
			+ " is the largest integer with " + math("h_d(n) \\le k_d(m) - r = " + (k - r)) + ".";
		if (points === 0) {
			return text + " Here the bound is just the length " + math("p_m = " + n) + ".";
		}
		let set;
		if (reason.set === "-") set = math("Z_{" + points + "}^-");
		else if (reason.set === "+") set = math("Z_{" + points + "}^+");
		else set = math("Z_{" + points + "}^-") + " (or " + math("Z_{" + points + "}^+") + ", which gives the same value)";
		return text + " The forms of degree " + math("d") + " vanishing on the set " + set + " of "
			+ math("n") + " points of " + math("\\mathbb{P}^{" + m + "}(\\mathbb{F}_{" + q + "})")
			+ " (described in [PRM, Section 6.2]) form a subcode of dimension at least " + math("r")
			+ ", supported on the remaining " + math("p_m - n = " + value) + " points.";
	}

	case "SJ24 Thm 7": {
		const a = reason.alpha, g = reason.gamma;
		return "By the recursive bound [SJ24, Thm 7], " + math("d_r \\ge \\min_{(\\alpha,\\gamma) \\in Y} B_{\\alpha,\\gamma}")
			+ ", where " + math("B_{\\alpha,\\gamma} = \\max\\{d_{r-\\gamma}(\\mathrm{RM}_q(d,m)),\\, d_{r-\\alpha}(\\mathrm{RM}_q(d-1,m))\\}"
				+ " + \\max\\{d_\\alpha(\\mathrm{PRM}_q(d,m-1)),\\, d_\\gamma(\\mathrm{PRM}_q(d-q+1,m-1))\\}")
			+ " (see [SJ24] for the set " + math("Y") + "). The minimum is attained at "
			+ math("(\\alpha,\\gamma) = (" + a + "," + g + ")") + ": "
			+ math("B_{" + a + "," + g + "} = \\max\\{" + reason.RM_d + "," + reason.RM_d_minus_1 + "\\} + \\max\\{"
				+ reason.same_degree + "," + reason.lower_degree + "\\} = " + value)
			+ ". Here " + math("d_{" + (r - g) + "}(" + RM(q, d, m) + ") = " + reason.RM_d)
			+ " and " + math("d_{" + (r - a) + "}(" + RM(q, d - 1, m) + ") = " + reason.RM_d_minus_1)
			+ " (Heijnen and Pellikaan [HP98], see [SJ24, Thm 6]), and we use "
			+ inputWeight(q, d, m - 1, a, reason.same_degree) + " and "
			+ inputWeight(q, d - q + 1, m - 1, g, reason.lower_degree) + ".";
	}

	case "computed": {
		let text = "Computed value [" + escapeHTML(reason.source) + "]";
		if (reason.note) text += ": " + escapeHTML(reason.note);
		return text;
	}

	default:
		return "Trivial bound.";
	}
}

function sameReason(a, b) {
	return JSON.stringify(a) === JSON.stringify(b);
}

function showExplanation(q, d, m, r) {
	const box = document.getElementById("ghw-explanation");
	const code = codeOf(q, d, m);
	if (!code || r < 1 || r > code.k) {
		box.hidden = true;
		return;
	}
	const lower = code.lower[r], upper = code.upper[r];
	const name = "d_{" + r + "}(" + PRM(q, d, m) + ")";
	let html = '<a class="ghw-close" href="' + address(q, m) + '" title="Close">&times;</a>';
	if (lower === upper) {
		html += "<h3>" + math(name + " = " + lower) + "</h3>";
	} else {
		html += "<h3>" + math(lower + " \\le " + name + " \\le " + upper) + "</h3>";
	}
	const lowerReason = code.lower_reason[r], upperReason = code.upper_reason[r];
	if (lower === upper && sameReason(lowerReason, upperReason)) {
		html += '<p><span class="ghw-kind">Exact value.</span> ' + explain(lowerReason, q, d, m, r, lower, code.k) + "</p>";
	} else {
		html += '<p><span class="ghw-kind">Lower bound ' + lower + ".</span> "
			+ explain(lowerReason, q, d, m, r, lower, code.k) + "</p>";
		html += '<p><span class="ghw-kind">Upper bound ' + upper + ".</span> "
			+ explain(upperReason, q, d, m, r, upper, code.k) + "</p>";
	}
	if (lower < upper && upperReason.rule === "PRM Thm 6.7") {
		html += "<p>[PRM, Conj 6.9] predicts that " + math(name + " = " + upper) + ".</p>";
	}
	html += '<p class="ghw-permalink">Link to this entry: <a href="' + address(q, m, d, r) + '">'
		+ escapeHTML(location.origin + location.pathname + address(q, m, d, r)) + "</a></p>";
	box.innerHTML = html;
	box.hidden = false;
	typeset(box);
}


// ---------------------------------------------------------------------------------------------
// The tables
// ---------------------------------------------------------------------------------------------

function entryText(code, r) {
	const lower = code.lower[r], upper = code.upper[r];
	return lower === upper ? String(lower) : lower + "–" + upper;
}

function gridHTML(q, m, code) {
	let html = '<div class="ghw-head"></div>';
	for (let b = 1; b <= COLUMNS; b++) html += '<div class="ghw-head">' + b + "</div>";
	for (let a = 0; a < code.k; a += COLUMNS) {
		html += '<div class="ghw-head">' + a + "</div>";
		for (let b = 1; b <= COLUMNS; b++) {
			const r = a + b;
			if (r > code.k) {
				html += "<div></div>";
				continue;
			}
			const open = code.lower[r] !== code.upper[r] ? " ghw-open" : "";
			html += '<a class="ghw-cell' + open + '" id="entry-' + code.d + "-" + r + '" href="'
				+ address(q, m, code.d, r) + '" title="d_' + r + '">' + entryText(code, r) + "</a>";
		}
	}
	return '<div class="ghw-grid">' + html + "</div>";
}

function isExpanded(code) {
	if (code.d in expanded) return expanded[code.d];
	return code.k <= EXPANDED_UP_TO;
}

function codeBlockHTML(q, m, code) {
	let exact = 0;
	for (let r = 1; r <= code.k; r++) if (code.lower[r] === code.upper[r]) exact += 1;
	const complete = exact === code.k;
	let title = math(PRM(q, code.d, m)) + ": " + code.k + " weights, ";
	title += complete ? "all known." : exact + " known, " + (code.k - exact) + " only bounded.";
	const open = isExpanded(code);
	title += ' <a class="ghw-toggle" data-degree="' + code.d + '">' + (open ? "Hide" : "Show") + "</a>";
	return '<div class="ghw-code ' + (complete ? "ghw-complete" : "ghw-partial") + '" id="code-' + code.d + '">'
		+ '<div class="ghw-code-label"><span class="ghw-degree">' + math("d = " + code.d) + "</span>"
		+ '<span class="ghw-dimension">' + math("k = " + code.k) + "</span></div>"
		+ '<div class="ghw-code-content"><div class="ghw-code-title">' + title + "</div>"
		+ '<div class="ghw-grid-wrapper">' + (open ? gridHTML(q, m, code) : "") + "</div></div></div>";
}

function drawChoices() {
	const qs = [...new Set(index.tables.map(t => t.q))];
	document.getElementById("ghw-q-choices").innerHTML = qs.map(q => {
		const ms = index.tables.filter(t => t.q === q).map(t => t.m);
		const m = shown && ms.includes(shown.m) ? shown.m : Math.min(...ms);
		const current = shown && shown.q === q ? " ghw-current" : "";
		return '<a class="ghw-choice' + current + '" href="' + address(q, m) + '">' + q + "</a>";
	}).join("");
	document.getElementById("ghw-m-choices").innerHTML = index.tables.filter(t => t.q === shown.q).map(t => {
		const current = t.m === shown.m ? " ghw-current" : "";
		return '<a class="ghw-choice' + current + '" href="' + address(t.q, t.m) + '">' + t.m + "</a>";
	}).join("");
}

function drawTable() {
	const {q, m, data} = shown;
	const info = tableInfo(q, m);
	const summary = document.getElementById("ghw-summary");
	summary.innerHTML = "Length " + math("p_" + m + " = " + data.n) + ". Codes " + math(PRM(q, "d", m))
		+ " with " + math("1 \\le d \\le " + Math.max(...info.degrees)) + ": " + info.weights + " weights, "
		+ info.exact + " known exactly"
		+ (info.exact < info.weights ? ", " + (info.weights - info.exact) + " only bounded." : ".");
	const container = document.getElementById("ghw-codes");
	container.innerHTML = data.codes.map(code => codeBlockHTML(q, m, code)).join("");
	typeset(summary);
	typeset(container);
}

function toggleCode(degree) {
	const code = codeOf(shown.q, degree, shown.m);
	expanded[degree] = !isExpanded(code);
	const block = document.getElementById("code-" + degree);
	block.outerHTML = codeBlockHTML(shown.q, shown.m, code);
	typeset(document.getElementById("code-" + degree));
}

function select(d, r) {
	document.querySelectorAll(".ghw-selected").forEach(cell => cell.classList.remove("ghw-selected"));
	if (d === null) {
		document.getElementById("ghw-explanation").hidden = true;
		return;
	}
	const code = codeOf(shown.q, d, shown.m);
	if (!code) return;
	if (!isExpanded(code)) toggleCode(d);
	showExplanation(shown.q, d, shown.m, r);
	const cell = document.getElementById("entry-" + d + "-" + r);
	if (cell) {
		cell.classList.add("ghw-selected");
		const box = cell.getBoundingClientRect();
		const panel = document.getElementById("ghw-explanation").getBoundingClientRect();
		if (box.top < panel.bottom || box.bottom > window.innerHeight) {
			window.scrollBy({top: box.top - panel.bottom - 20, behavior: "smooth"});
		}
	}
}


// ---------------------------------------------------------------------------------------------
// Following the address of the page
// ---------------------------------------------------------------------------------------------

async function follow() {
	const params = new URLSearchParams(location.hash.slice(1));
	if (location.hash && !params.has("q")) return;      // an ordinary anchor, such as #references
	let q = Number(params.get("q")), m = Number(params.get("m"));
	if (!tableInfo(q, m)) {                               // default: q = 3, m = 3
		q = 3;
		m = 3;
	}
	if (!shown || shown.q !== q || shown.m !== m) {
		const data = await download(tableInfo(q, m).file);
		shown = {q, m, data};
		for (const key in expanded) delete expanded[key];
		drawChoices();
		drawTable();
	}
	if (params.has("d") && params.has("r")) {
		select(Number(params.get("d")), Number(params.get("r")));
	} else {
		select(null, null);
	}
}

function drawReferences() {
	const list = document.getElementById("ghw-references");
	list.innerHTML = Object.entries(index.references).map(([key, ref]) => {
		const link = ref.link ? ' <a href="' + escapeHTML(ref.link) + '" target="_blank" rel="noopener noreferrer">'
			+ escapeHTML(ref.link.replace("https://doi.org/", "doi:")) + "</a>" : "";
		return "<li><strong>[" + escapeHTML(key) + "]</strong> " + escapeHTML(ref.citation) + link + "</li>";
	}).join("");
}

async function start() {
	try {
		index = await download("index.json");
	} catch (error) {
		document.getElementById("ghw-loading").textContent = "The tables could not be loaded.";
		return;
	}
	drawReferences();
	document.getElementById("ghw-codes").addEventListener("click", event => {
		const toggle = event.target.closest(".ghw-toggle");
		if (toggle) {
			event.preventDefault();
			toggleCode(Number(toggle.dataset.degree));
		}
	});
	window.addEventListener("hashchange", follow);
	await follow();
}

start();
