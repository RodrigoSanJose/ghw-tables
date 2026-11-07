/*
	Tables of generalized Hamming weights of projective Reed-Muller codes.

	This script only DISPLAYS the tables; they are computed by src/generate.py and stored in data/:
	  - data/index.json lists the tables (one for each pair q, m) and the references;
	  - data/q{q}_m{m}.json contains, for every code PRM_q(d,m), the lists lower, upper,
	    lower_reason and upper_reason, indexed by r (position 0 holds d_0 = 0).

	The address of the page says what is shown:
	  #q=3&m=3            the table for q = 3, m = 3;
	  #q=3&m=3&d=4        the same table, scrolled to the code PRM_3(4,3);
	  #q=3&m=3&d=4&r=7    the same table, with the entry d_7(PRM_3(4,3)) selected and explained.
	So every entry has its own link, and the links in the explanations are ordinary links.
*/

"use strict";

const COLUMNS = 10;            // row i and column j of a grid hold d_{i+j}, for j = 1, ..., 10
const EXPANDED_UP_TO = 60;     // codes with at most this many weights are shown expanded

let index = null;              // the contents of data/index.json
const downloaded = {};         // file name -> its contents (a promise), for the files already requested
let shown = null;              // {q, m, data}: the table currently shown
const expanded = {};           // "d" -> true or false, for the codes expanded or collapsed by hand
let followCount = 0;           // the number of calls of follow(), to ignore out-of-date ones


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

function address(q, m, d, r) {             // the link to a table, a code, or an entry
	let hash = "#q=" + q + "&m=" + m;
	if (d !== undefined) hash += "&d=" + d;
	if (r !== undefined) hash += "&r=" + r;
	return hash;
}

function analyticsAttributes(action, q, m, d, r) {
	// The shared delegated tracker also covers links added by later renders. Keep mathematical
	// context in metadata, rather than trying to recover it from MathJax's generated elements.
	const name = "GHW. " + action;
	const context = Object.entries({q, m, d, r}).filter(([, value]) => value !== undefined);
	const label = name + ". " + context.map(([key, value]) => key + "=" + value).join(", ");
	return ' data-analytics-name="' + escapeHTML(name) + '" data-analytics-label="' + escapeHTML(label)
		+ '" aria-label="' + escapeHTML(label) + '"'
		+ context.map(([key, value]) => ' data-analytics-' + key + '="' + value + '"').join("");
}

function referenceTitle(ref) {
	// Canonical titles come from references.csv. Legacy data keeps the remaining citation after
	// author initials: bibliographic detail is preferable to cutting off a title containing commas.
	const title = ref.title || ref.citation.replace(/^(?:(?:[A-Z]\.\s*)+[^,]+,\s*)+/, "") || ref.citation;
	return title.replace(/[–—]/g, "-");   // match publication names on the personal website
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

const typesetting = new WeakMap();       // element -> number of typesettings of it not finished yet

function typeset(element) {
	// Ask MathJax to typeset new content.  If MathJax has not started yet, there is nothing to do:
	// when it starts, it typesets the whole page, whose math stays hidden until then (index.html).
	// Otherwise we wait until it is ready.  Meanwhile the math of the element is hidden too (the class
	// mj-pending, see ghw.css), so that its TeX source never shows, also after changing q or m.
	if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
		typesetting.set(element, (typesetting.get(element) || 0) + 1);
		element.classList.add("mj-pending");
		MathJax.startup.promise = MathJax.startup.promise
			.then(() => MathJax.typesetPromise([element]))
			.catch(error => console.log("MathJax: " + error.message))
			.finally(() => {                     // show it after the last typesetting asked for it
				typesetting.set(element, typesetting.get(element) - 1);
				if (typesetting.get(element) === 0) element.classList.remove("mj-pending");
			});
	}
}

function afterTypesetting(action) {
	// Run action once MathJax has typeset everything: typesetting changes the height of the text,
	// and so the place of the cells.  Before the page has finished loading, MathJax may not have
	// started yet, so we wait for the "load" event; if MathJax could not be loaded, we do not wait.
	if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
		MathJax.startup.promise.finally(action);
	} else if (document.readyState !== "complete") {
		window.addEventListener("load", () => afterTypesetting(action), {once: true});
	} else {
		action();
	}
}

function download(file) {                  // the contents of data/file, requested only once
	if (!(file in downloaded)) {
		downloaded[file] = fetch("data/" + file).then(response => {
			if (!response.ok) throw new Error(file + ": " + response.status);
			return response.json();
		});
		downloaded[file].catch(() => { delete downloaded[file]; });    // after an error, try again next time
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
	return '<a href="' + address(q, mm, dd, alpha) + '"' + analyticsAttributes("Referenced weight", q, mm, dd, alpha)
		+ '>' + math(name + " \\ge " + value) + "</a>";
}

function explain(reason, q, d, m, r, value, k) {
	const n = p(q, m);
	switch (reason.rule) {

	case "SJ26 Thm. 1.1": {
		const mu = reason.mu;              // mu[0] is mu_1, ..., mu[d-1] is mu_d
		const tuple = d === 1 ? "\\mu_1 = " + mu[0]
			: "(\\mu_1,\\dots,\\mu_" + d + ") = (" + mu.join(",") + ")";
		const terms = [p(q, mu[d - 1])];   // p_{mu_d}, then floor(q^mu_i) for i < d
		for (let i = 0; i < d - 1; i++) terms.push(mu[i] >= 0 ? q ** mu[i] : 0);
		return "Since " + math("d < q") + ", the weight is given by [SJ26, Thm. 1.1], conjectured by Beelen, Datta"
			+ " and Ghorpade [BDG22]: if " + math("(\\mu_1,\\dots,\\mu_d)") + " is the Macaulay tuple of "
			+ math("\\binom{m+d}{d} - r = " + (binomial(m + d, d) - r)) + " in degree " + math("d")
			+ ", then " + math("d_r = p_m - p_{\\mu_d} - \\sum_{i=1}^{d-1} \\lfloor q^{\\mu_i} \\rfloor")
			+ ". Here " + math(tuple) + ", so " + math("d_r = " + n + " - " + terms.join(" - ") + " = " + value) + ".";
	}

	case "SJ26 Cor. 4.2": {
		const e = reason.dual_degree;
		return "Since " + math("(m-1)(q-1) < d < m(q-1)") + ", the dual code is "
			+ '<a href="' + address(q, m, e) + '"' + analyticsAttributes("Referenced code", q, m, e) + '>' + math(PRM(q, e, m)) + "</a>"
			+ " [Sør91], whose weights are given by [SJ26, Thm. 1.1] because " + math(e + " < q")
			+ ". By Wei duality [Wei91], " + math("d_r") + " is the " + math("r") + "-th integer of "
			+ math("\\{1,\\dots,p_m\\}") + " that is not of the form " + math("p_m + 1 - d_s(" + PRM(q, e, m) + ")")
			+ " [SJ26, Cor. 4.2].";
	}

	case "whole space":
		return "Since " + math("d > m(q-1)") + ", the code is the whole space "
			+ math("\\mathbb{F}_{" + q + "}^{" + n + "}") + ", so " + math("d_r = r") + ".";

	case "dual is all-ones":
		return "Since " + math("d = m(q-1)") + ", the dual code is spanned by the all-ones vector [Sør91],"
			+ " and Wei duality [Wei91] gives " + math("d_r = r + 1") + ".";

	case "Sorensen":
		return "This is the minimum distance of " + math(PRM(q, d, m)) + ", computed by Sørensen [Sør91].";

	case "SJ26 Prop. 6.12": {
		let text = "Given by [SJ26, Prop. 6.12], which determines the first weights when ";
		if ((d - 1) % (q - 1) === 0) {                         // case (a): d = 1 + t(q-1)
			const t = (d - 1) / (q - 1), h = m - t;
			text += math("d = 1 + t(q-1)") + ": here " + math("t = " + t) + ", " + math("h = m - t = " + h)
				+ " and " + math("d_r = q^h + q^{h-1} + \\dots + q^{h-r+1} = " + value) + ".";
		} else {                                               // case (b): d = 2 + t(q-1), q >= 3
			const t = (d - 2) / (q - 1), h = m - t;
			const formula = r <= h ? "d_r = q^h - q^{h-r} = " : "d_{h+1} = q^h = ";
			text += math("d = 2 + t(q-1)") + " and " + math("q \\ge 3") + ": here " + math("t = " + t) + ", "
				+ math("h = m - t = " + h) + " and " + math(formula + value) + ".";
		}
		return text;
	}

	case "SJ26 Thm. 6.7": {
		const points = reason.n;
		let text = "By [SJ26, Thm. 6.7], " + math("d_r \\le B_r(q,d,m) = p_m - n") + ", where " + math("n = " + points)
			+ " is the largest integer " + math("0 \\le n \\le p_m") + " with "
			+ math("h_d(n) \\le k_d(m) - r = " + (k - r)) + ".";
		if (points === 0) {
			return text + " Here the bound is just the length " + math("p_m = " + n) + ".";
		}
		let set;
		if (reason.set === "-") set = math("Z_{" + points + "}^-");
		else if (reason.set === "+") set = math("Z_{" + points + "}^+");
		else set = math("Z_{" + points + "}^-") + " (or " + math("Z_{" + points + "}^+") + ", which gives the same value)";
		return text + " The evaluations of the forms of degree " + math("d") + " vanishing on the set " + set
			+ " of " + math("n") + " points of " + math("\\mathbb{P}^{" + m + "}(\\mathbb{F}_{" + q + "})")
			+ " (described in [SJ26, Section 6.2]) form a subcode of dimension at least " + math("r")
			+ ", supported on the remaining " + math("p_m - n = " + value) + " points.";
	}

	case "SJ24 Thm. 7": {
		const a = reason.alpha, g = reason.gamma;
		return "By the recursive bound [SJ24, Thm. 7], " + math("d_r \\ge \\min_{(\\alpha,\\gamma) \\in Y} B_{\\alpha,\\gamma}")
			+ ", where " + math("B_{\\alpha,\\gamma} = \\max\\{d_{r-\\gamma}(\\mathrm{RM}_q(d,m)),\\, d_{r-\\alpha}(\\mathrm{RM}_q(d-1,m))\\}"
				+ " + \\max\\{d_\\alpha(\\mathrm{PRM}_q(d,m-1)),\\, d_\\gamma(\\mathrm{PRM}_q(d-q+1,m-1))\\}")
			+ " (see [SJ24] for the set " + math("Y") + "). The minimum is attained at "
			+ math("(\\alpha,\\gamma) = (" + a + "," + g + ")") + ": "
			+ math("B_{" + a + "," + g + "} = \\max\\{" + reason.RM_d + "," + reason.RM_d_minus_1 + "\\} + \\max\\{"
				+ reason.PRM_d + "," + reason.PRM_d_minus_q_plus_1 + "\\} = " + value)
			+ ". Here " + math("d_{" + (r - g) + "}(" + RM(q, d, m) + ") = " + reason.RM_d)
			+ " and " + math("d_{" + (r - a) + "}(" + RM(q, d - 1, m) + ") = " + reason.RM_d_minus_1)
			+ " (Heijnen and Pellikaan [HP98], see [SJ24, Thm. 6]), and we use "
			+ inputWeight(q, d, m - 1, a, reason.PRM_d) + " and "
			+ inputWeight(q, d - q + 1, m - 1, g, reason.PRM_d_minus_q_plus_1) + ".";
	}

	case "Wei duality": {
		const e = reason.dual_degree, w = reason.w, count = reason.count;
		const N = w - (n - k) + count;
		const link = '<a href="' + address(q, m, e) + '"' + analyticsAttributes("Referenced code", q, m, e) + '>' + math(PRM(q, e, m)) + "</a>";
		const dual = reason.plus_ones ? PRM(q, d, m) + "^\\perp" : PRM(q, e, m);
		let text;
		if (reason.plus_ones) {
			text = "Since " + math("q - 1") + " divides " + math("d") + ", the dual code is "
				+ math(dual + " = " + PRM(q, e, m) + " + \\langle (1, \\dots, 1) \\rangle") + " [Sør91]. It contains "
				+ link + " with codimension one, and a subspace of the dual of dimension " + math("s")
				+ " meets " + math(PRM(q, e, m)) + " in dimension at least " + math("s - 1") + ", so "
				+ math("d_{s-1}(" + PRM(q, e, m) + ") \\le d_s(" + dual + ") \\le d_s(" + PRM(q, e, m) + ")") + ".";
		} else {
			text = "The dual code is " + link + " [Sør91].";
		}
		text += " By Wei duality [Wei91; SJ24, Thm. 9], the number " + math("N(w)") + " of weights of "
			+ math(PRM(q, d, m)) + " that are at most " + math("w") + " is "
			+ math("N(w) = w - (p_m - k) + \\#\\{s : d_s(" + dual + ") \\le p_m - w\\}") + ". Take "
			+ math("w = " + w) + ", so that " + math("p_m - w = " + (n - w)) + ": ";
		if (reason.bound === "upper") {
			text += "the upper bounds of " + link + " show that at least " + math(String(count)) + " of its weights are at most "
				+ math(String(n - w));
			if (reason.plus_ones) text += ", and hence so are at least " + math(String(count)) + (count === 1 ? " weight" : " weights") + " of the dual";
			text += ". So " + math("N(" + w + ") \\ge " + w + " - " + (n - k) + " + " + count + " = " + N
				+ " \\ge r") + ", that is, " + math("d_r \\le " + w) + ".";
		} else {
			const few = c => (c === 0 ? "none" : "at most " + math(String(c)));     // "none" instead of "at most 0"
			text += "the lower bounds of " + link + " show that " + few(reason.plus_ones ? count - 1 : count)
				+ " of its weights can be at most " + math(String(n - w));
			if (reason.plus_ones) text += ", and hence at most " + math(String(count)) + (count === 1 ? " weight" : " weights") + " of the dual";
			text += ". So " + math("N(" + w + ") \\le " + w + " - " + (n - k) + " + " + count + " = " + N
				+ " \\le r - 1") + ", that is, " + math("d_r \\ge " + (w + 1)) + ".";
		}
		if (!reason.plus_ones) text += " This is how duality improves the tables of the recursive bound in [SJ24, Section V-C].";
		return text;
	}

	case "fundamental relation": {
		// The relation (q^j - q) d_j >= (q^j - 1) d_{j-1}: with j = r for a lower bound (from d_{r-1}),
		// and with j = r + 1 for an upper bound (from d_{r+1}).
		const s = reason.from_r, b = reason.from_bound;
		const link = '<a href="' + address(q, m, d, s) + '"' + analyticsAttributes("Referenced weight", q, m, d, s) + '>';
		const text = "By the fundamental relation " + math("(q^j - q)\\, d_j \\ge (q^j - 1)\\, d_{j-1}")
			+ ", valid for every linear code [HKLY95, Thm. 1] ([HKY92, Thm. 1] for " + math("q = 2")
			+ "), which also shows that the weights increase strictly. ";
		if (s < r) {
			return text + "With " + math("j = r = " + r) + " and " + link + math("d_{" + s + "} \\ge " + b) + "</a>, "
				+ math("d_r \\ge \\left\\lceil \\frac{(" + q + "^{" + r + "} - 1) \\cdot " + b + "}{" + q + "^{" + r + "} - " + q
					+ "} \\right\\rceil = " + value) + ".";
		}
		return text + "With " + math("j = r + 1 = " + s) + " and " + link + math("d_{" + s + "} \\le " + b) + "</a>, "
			+ math("d_r \\le \\left\\lfloor \\frac{(" + q + "^{" + s + "} - " + q + ") \\cdot " + b + "}{" + q + "^{" + s
				+ "} - 1} \\right\\rfloor = " + value) + ".";
	}

	case "residual code": {
		// The bound for the pair (d_j, d_{j+1}): j = r - 1 for an upper bound (from d_{r-1}, possibly
		// d_0 = 0), and j = r for a lower bound (from d_{r+1}).  reason.total is the sum that exceeds p_m.
		const s = reason.from_r, b = reason.from_bound, total = reason.total;
		const link = '<a href="' + address(q, m, d, s) + '"' + analyticsAttributes("Referenced weight", q, m, d, s) + '>';
		let text = "By the residual code bound, valid for every linear code [HKLY95, proof of Thm. 4]: if a subcode of"
			+ " dimension " + math("j") + " is supported on " + math("d_j") + " coordinates, deleting them from all the"
			+ " codewords gives a code of length " + math("p_m - d_j") + ", dimension " + math("k - j")
			+ " and minimum distance at least " + math("d_{j+1} - d_j") + ", so by the Griesmer bound "
			+ math("p_m \\ge d_j + \\sum_{i=0}^{k-j-1} \\lceil (d_{j+1} - d_j)/q^i \\rceil") + ". The right-hand side"
			+ " does not decrease when " + math("d_{j+1}") + " grows, and does not increase when " + math("d_j")
			+ " grows (its term " + math("i = 0") + " is " + math("d_{j+1} - d_j") + "). ";
		if (s < r) {
			const from = s === 0 ? math("d_0 = 0") + " (this case is the Griesmer bound)"
				: link + math("d_{" + s + "} \\le " + b) + "</a>";
			return text + "With " + math("j = r - 1 = " + s) + " and " + from + ": if " + math("d_r \\ge " + (value + 1))
				+ ", then " + math("p_m \\ge " + b + " + \\sum_{i=0}^{" + (k - s - 1) + "} \\lceil " + (value + 1 - b) + "/"
					+ q + "^i \\rceil = " + total) + ", which is false because " + math("p_m = " + n) + ". So "
				+ math("d_r \\le " + value) + ".";
		}
		return text + "With " + math("j = r = " + r) + " and " + link + math("d_{" + s + "} \\ge " + b) + "</a>: if "
			+ math("d_r \\le " + (value - 1)) + ", then " + math("p_m \\ge " + (value - 1) + " + \\sum_{i=0}^{" + (k - r - 1)
				+ "} \\lceil " + (b - value + 1) + "/" + q + "^i \\rceil = " + total) + ", which is false because "
			+ math("p_m = " + n) + ". So " + math("d_r \\ge " + value) + ".";
	}

	case "computed": {
		let text = "Source: [" + escapeHTML(reason.source) + "].";
		if (reason.note) text += " " + escapeHTML(reason.note);
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
	let html = '<a class="ghw-close" href="' + address(q, m) + '" title="Close"'
		+ analyticsAttributes("Close explanation", q, m, d, r) + '>&times;</a>';
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
	if (lower < upper && upperReason.rule === "SJ26 Thm. 6.7") {
		html += "<p>[SJ26, Conj. 6.9] predicts that " + math(name + " = " + upper) + ".</p>";
	}
	html += '<p class="ghw-permalink">Link to this entry: <a href="' + address(q, m, d, r) + '"'
		+ analyticsAttributes("Entry permalink", q, m, d, r) + '>'
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
	for (let j = 1; j <= COLUMNS; j++) html += '<div class="ghw-head">' + j + "</div>";
	for (let i = 0; i < code.k; i += COLUMNS) {
		html += '<div class="ghw-head">' + i + "</div>";
		for (let j = 1; j <= COLUMNS; j++) {
			const r = i + j;
			if (r > code.k) {
				html += "<div></div>";
				continue;
			}
			const open = code.lower[r] !== code.upper[r] ? " ghw-open" : "";
			html += '<a class="ghw-cell' + open + '" id="entry-' + code.d + "-" + r + '" href="'
				+ address(q, m, code.d, r) + '" title="d_' + r + '"'
				+ analyticsAttributes("Open explanation", q, m, code.d, r) + '>' + entryText(code, r) + "</a>";
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
	title += ' <a class="ghw-toggle" href="#" role="button" data-degree="' + code.d + '"'
		+ analyticsAttributes(open ? "Hide weights" : "Show weights", q, m, code.d) + '>'
		+ (open ? "Hide" : "Show") + "</a>";
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
		return '<a class="ghw-choice' + current + '" href="' + address(q, m) + '"'
			+ analyticsAttributes("Select field size", q, m) + '>' + q + "</a>";
	}).join("");
	document.getElementById("ghw-m-choices").innerHTML = index.tables.filter(t => t.q === shown.q).map(t => {
		const current = t.m === shown.m ? " ghw-current" : "";
		return '<a class="ghw-choice' + current + '" href="' + address(t.q, t.m) + '"'
			+ analyticsAttributes("Select dimension", t.q, t.m) + '>' + t.m + "</a>";
	}).join("");
}

function drawTable() {
	const {q, m, data} = shown;
	const info = tableInfo(q, m);
	const summary = document.getElementById("ghw-summary");
	summary.innerHTML = "Length " + math("p_" + m + " = " + data.n) + ". Codes " + math(PRM(q, "d", m))
		+ " with " + math("1 \\le d \\le " + Math.max(...info.degrees)) + ": " + info.weights + " weights, "
		+ info.exact + " known exactly"
		+ (info.exact < info.weights ? ", " + (info.weights - info.exact) + " only bounded." : ".")
		+ (q === 2 ? " Note: for " + math("q=2") + " PRM codes are shortened RM codes at the origin." : "")
		+ ' <span class="ghw-all-toggles" data-analytics-section="GHW tables / Controls">'
		+ '<button type="button" class="ghw-all-toggle" data-show="true"' + analyticsAttributes("Show all weights", q, m)
		+ ">Show all</button> · "
		+ '<button type="button" class="ghw-all-toggle" data-show="false"' + analyticsAttributes("Hide all weights", q, m)
		+ ">Hide all</button></span>";
	const container = document.getElementById("ghw-codes");
	container.innerHTML = data.codes.map(code => codeBlockHTML(q, m, code)).join("");
	typeset(summary);
	typeset(container);
}

function highlightSelected() {             // mark the entry selected in the address, if it is drawn
	const params = new URLSearchParams(location.hash.slice(1));
	if (params.has("d") && params.has("r")) {
		const cell = document.getElementById("entry-" + Number(params.get("d")) + "-" + Number(params.get("r")));
		if (cell) cell.classList.add("ghw-selected");
	}
}

function toggleCode(degree, keepFocus) {
	const code = codeOf(shown.q, degree, shown.m);
	expanded[degree] = !isExpanded(code);
	const block = document.getElementById("code-" + degree);
	block.outerHTML = codeBlockHTML(shown.q, shown.m, code);
	typeset(document.getElementById("code-" + degree));
	highlightSelected();
	if (keepFocus) document.querySelector("#code-" + degree + " .ghw-toggle").focus();
}

function showAll(show) {                   // the buttons "Show all" and "Hide all" of the summary
	for (const code of shown.data.codes) expanded[code.d] = show;
	const container = document.getElementById("ghw-codes");    // the summary, with the buttons, stays
	container.innerHTML = shown.data.codes.map(code => codeBlockHTML(shown.q, shown.m, code)).join("");
	highlightSelected();
	typeset(container);
}

function showCode(d) {                     // expand the block of PRM_q(d,m) and scroll to it
	const code = codeOf(shown.q, d, shown.m);
	if (!code) return;
	if (!isExpanded(code)) toggleCode(d);
	afterTypesetting(() => document.getElementById("code-" + d).scrollIntoView({behavior: "smooth"}));
}

function showSelectedCell() {
	// If the selected cell is hidden, scroll its grid sideways (on narrow screens), and scroll the
	// page so that the cell appears just below the explanation, which then sticks to the top.
	const cell = document.querySelector(".ghw-selected");
	if (!cell) return;
	const wrapper = cell.closest(".ghw-grid-wrapper");
	const grid = wrapper.getBoundingClientRect();
	let box = cell.getBoundingClientRect();
	if (box.left < grid.left || box.right > grid.right) {
		wrapper.scrollLeft += box.left - grid.left - (grid.width - box.width) / 2;
		box = cell.getBoundingClientRect();
	}
	const panel = document.getElementById("ghw-explanation");
	if (box.top < panel.getBoundingClientRect().bottom || box.bottom > window.innerHeight) {
		cell.style.scrollMarginTop = (panel.offsetHeight + 20) + "px";
		cell.scrollIntoView({block: "start", behavior: "smooth"});
	}
}

function select(d, r) {
	document.querySelectorAll(".ghw-selected").forEach(cell => cell.classList.remove("ghw-selected"));
	const box = document.getElementById("ghw-explanation");
	const code = d === null ? null : codeOf(shown.q, d, shown.m);
	if (!code || r < 1 || r > code.k) {    // nothing selected, or an entry that does not exist
		box.hidden = true;
		return;
	}
	if (!isExpanded(code)) toggleCode(d);
	showExplanation(shown.q, d, shown.m, r);
	const cell = document.getElementById("entry-" + d + "-" + r);
	if (cell) {
		cell.classList.add("ghw-selected");
		afterTypesetting(showSelectedCell);
	}
}


// ---------------------------------------------------------------------------------------------
// Following the address of the page
// ---------------------------------------------------------------------------------------------

async function follow() {
	const call = ++followCount;
	const params = new URLSearchParams(location.hash.slice(1));
	const anchor = location.hash !== "" && !params.has("q");   // an ordinary anchor, such as #references
	if (anchor && shown) return;                                 // keep the table; the browser scrolls
	let q = Number(params.get("q")), m = Number(params.get("m"));
	const notice = document.getElementById("ghw-notice");
	notice.hidden = true;
	let missing = false;
	if (!tableInfo(q, m)) {                                      // default: q = 3, m = 3
		missing = params.has("q");
		if (missing) {
			notice.textContent = "There is no table for q = " + params.get("q") + " and m = " + (params.get("m") || "?")
				+ " in this version; the table for q = 3 and m = 3 is shown instead.";
			notice.hidden = false;
		}
		q = 3;
		m = 3;
	}
	if (!shown || shown.q !== q || shown.m !== m) {
		const data = await download(tableInfo(q, m).file);
		if (call !== followCount) return;                        // the address changed meanwhile
		shown = {q, m, data};
		for (const key in expanded) delete expanded[key];
		drawChoices();
		drawTable();
	}
	if (anchor) {                                                // opened at an anchor: the table
		const target = document.getElementById(location.hash.slice(1));   // has pushed it down
		if (target) afterTypesetting(() => target.scrollIntoView());
	} else if (missing) {
		select(null, null);
	} else if (params.has("d") && params.has("r")) {
		select(Number(params.get("d")), Number(params.get("r")));
	} else if (params.has("d")) {                                // a code, such as #q=3&m=3&d=4
		select(null, null);
		showCode(Number(params.get("d")));
	} else {
		select(null, null);
	}
}

function drawReferences() {
	const list = document.getElementById("ghw-references");
	// Titles and optional concise aliases are exported from the same reference data as citations.
	// The shared tracker also bounds future titles without aliases, retaining the destination type.
	list.innerHTML = Object.entries(index.references).map(([key, ref]) => {
		const link = ref.link ? ' <a href="' + escapeHTML(ref.link) + '" target="_blank" rel="noopener noreferrer">'
			+ escapeHTML(ref.link.replace("https://doi.org/", "doi:")) + "</a>" : "";
		return '<li data-publication-title="' + escapeHTML(referenceTitle(ref)) + '" data-publication-short="'
			+ escapeHTML(ref.short_title || referenceTitle(ref)) + '"><strong>['
			+ escapeHTML(key) + "]</strong> " + escapeHTML(ref.citation) + link + "</li>";
	}).join("");
}

// The citation.  The button in the corner of the box copies exactly the BibTeX entry shown on the page.
function setUpCitation() {
	const button = document.getElementById("ghw-copy-bibtex");
	const status = document.getElementById("ghw-copy-status");
	const entry = document.querySelector("#ghw-bibtex code");
	if (!button || !status || !entry) return;
	const icon = button.querySelector("i");
	let timer = null;
	button.addEventListener("click", async () => {
		clearTimeout(timer);
		try {
			await navigator.clipboard.writeText(entry.textContent);
			status.textContent = "Copied.";
			if (icon) icon.className = "fa-solid fa-check";
		} catch (error) {
			// Without access to the clipboard, select the entry so that it can be copied by hand.
			const range = document.createRange();
			range.selectNodeContents(entry);
			const selection = window.getSelection();
			selection.removeAllRanges();
			selection.addRange(range);
			status.textContent = "The entry is selected: press Ctrl+C (⌘+C on a Mac) to copy it.";
		}
		timer = setTimeout(() => {                 // back to the copy icon after a moment
			status.textContent = "";
			if (icon) icon.className = "fa-regular fa-copy";
		}, status.textContent === "Copied." ? 2000 : 8000);
	});
}

async function start() {
	// The table of the address is requested at the same time as index.json, which lists the tables:
	// its file name is known (q{q}_m{m}.json), so the two downloads need not wait for each other.
	const params = new URLSearchParams(location.hash.slice(1));
	download("q" + Number(params.get("q") || 3) + "_m" + Number(params.get("m") || 3) + ".json").catch(() => {});
	try {
		index = await download("index.json");
	} catch (error) {
		document.getElementById("ghw-loading").textContent = "The tables could not be loaded.";
		return;
	}
	drawReferences();
	const codes = document.getElementById("ghw-codes");
	codes.addEventListener("click", event => {
		const toggle = event.target.closest(".ghw-toggle");
		if (toggle) {
			event.preventDefault();
			toggleCode(Number(toggle.dataset.degree), true);
		}
	});
	codes.addEventListener("keydown", event => {               // the space bar also works on Show/Hide
		const toggle = event.target.closest(".ghw-toggle");
		if (toggle && event.key === " ") {
			event.preventDefault();
			toggle.click();                // use the same activation path as mouse and Enter
		}
	});
	document.getElementById("ghw-summary").addEventListener("click", event => {
		const button = event.target.closest(".ghw-all-toggle");     // native buttons: Enter and Space too
		if (button && shown) showAll(button.dataset.show === "true");
	});
	window.addEventListener("hashchange", follow);
	await follow();
}

setUpCitation();
start();
