package com.chessnote.core

val boardJs: String = listOf(    // Taken from desktop templates/board.js (interactive board); do not modify
    """(function () {
    const data = JSON.parse(document.getElementById("boardData").textContent);
    const startFen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    const flipped = data.o === "black";
    const boards = [];    // Boards created so far; all reset before printing
    const pendingInits = [];    // Line cards not yet expanded; initialized together before printing
    const infoByIdx = {};    // Move index -> split result of that PGN text

    // ### PGN text: split moves, trim the shared prefix ###

    function tokenizePgn(text) {    // Returns each move's position in the text; skips comments, variations, NAGs, move numbers and results
        const tokens = [];
        const n = text.length;
        let i = 0;
        let numStart = -1;    // Start of the move number right before a move; kept when trimming
        while (i < n) {
            const ch = text[i];
            if (/\s/.test(ch)) {
                i++;
            } else if (ch === "{" || ch === "[") {
                const end = text.indexOf(ch === "{" ? "}" : "]", i);
                i = end < 0 ? n : end + 1;
            } else if (ch === ";") {
                const end = text.indexOf("\n", i);
                i = end < 0 ? n : end + 1;
            } else if (ch === "(") {
                let depth = 0;
                while (i < n) {
                    if (text[i] === "(") {
                        depth++;
                    } else if (text[i] === ")" && --depth === 0) {
                        i++;
                        break;
                    }
                    i++;
                }
            } else if (ch === "${'$'}") {
                i++;
                while (i < n && /\d/.test(text[i])) {
                    i++;
                }
            } else {
                let j = i;
                while (j < n && !/[\s{};(\[${'$'}]/.test(text[j])) {
                    j++;
                }
                if (j === i) {
                    j++;    // Stray symbols such as } are skipped so the loop always advances
                }
                let word = text.slice(i, j);
                let start = i;
                const m = /^(\d+\.+)(.*)${'$'}/.exec(word);
                if (m) {
                    numStart = numStart < 0 ? i : numStart;
                    start = i + m[1].length;
                    word = m[2];
                } else if (/^\.+${'$'}/.test(word)) {
                    numStart = numStart < 0 ? i : numStart;
                    word = "";
                }
                if (/^(1-0|0-1|1\/2-1\/2|\*)${'$'}/.test(word)) {
                    word = "";
                    numStart = -1;
                }
                if (word) {
                    tokens.push({numStart: numStart >= 0 ? numStart : start, start: start, end: j});
                    numStart = -1;
                }
                i = j;
            }
        }
        return tokens;
    }

    function moveNumberPrefix(idx, text, tokens, firstShown) {    // If the first move after trimming has no move number, add one (e.g. 6...Kxf7); spacing follows the original text
        if (tokens[firstShown].numStart < tokens[firstShown].start) {
            return "";
        }
        const fen = (data.l[idx][0] || startFen).split(" ");
        const ordinal = firstShown + (fen[1] === "b" ? 1 : 0);    // Even = white to move
        const number = (+fen[5] || 1) + Math.floor(ordinal / 2);
        const compact = tokens.some(tk => tk.numStart < tk.start && !/\s${'$'}/.test(text.slice(tk.numStart, tk.start)));
        return number + (ordinal % 2 ? "..." : ".") + (compact ? "" : " ");
    }

    function fillMoves(info) {    // Rebuild the text with each move wrapped in a span; moves before firstShown (shared with the starting PGN) are hidden
        const container = info.container;
        container.textContent = info.prefix;
        let pos = info.firstShown > 0 ? info.tokens[info.firstShown].numStart : 0;
        for (let j = info.firstShown; j < info.tokens.length; j++) {
            const tk = info.tokens[j];
            container.appendChild(document.createTextNode(info.text.slice(pos, tk.start)));
            const span = document.createElement("span");
            span.className = "pgn-mv";
            span.dataset.j = j;
            span.textContent = info.text.slice(tk.start, tk.end);
            container.appendChild(span);
            info.spans[j] = span;
            pos = tk.end;
        }
        container.appendChild(document.createTextNode(info.text.slice(pos)));
    }

    function preparePgn() {
        document.querySelectorAll(".pgn-block[data-idx], .line-card[data-idx]").forEach(el => {
            const idx = +el.dataset.idx;
            const isCard = el.classList.contains("line-card");
            const container = el.querySelector(isCard ? ".expanded .pgn-text" : ".pgn-text");
            const text = container.textContent;
            const tokens = tokenizePgn(text);
            const skip = data.l[idx][2];
            const cut = data.l[idx][3];
            const valid = tokens.length > 0 && tokens.length === lineMoves(idx).length - (cut ? 0 : skip);    // If the move count doesn't match, skip marking and trimming
            const firstShown = valid && cut ? skip : 0;
            const info = {text: text, tokens: tokens, valid: valid, container: container, spans: [], cur: null,
                base: cut ? 0 : skip, firstShown: firstShown, prefix: firstShown > 0 ? moveNumberPrefix(idx, text, tokens, firstShown) : ""};
            infoByIdx[idx] = info;
            if (!valid) {
                return;
            }
            fillMoves(info);
            if (isCard && info.firstShown > 0) {
                el.querySelector(".collapsed .pgn-text").textContent = info.prefix + text.slice(tokens[info.firstShown].numStart);
            }
        });
    }

    function fitCollapsed() {    // When the collapsed row overflows, show '.....' on the right
        const rows = [...document.querySelectorAll(".line-card:not([open]) .collapsed")];
        rows.forEach(row => row.classList.remove("is-clipped"));
        const clipped = rows.filter(row => {
            const mark = row.querySelector(".pgn-mark");
            return mark.scrollWidth > mark.clientWidth;
        });
        clipped.forEach(row => row.classList.add("is-clipped"));
    }

    // ### Positions and moves ###

    function sqIndex(name) {    // Position format: {b: 64-square array (a1 = 0, h8 = 63), t: "w" | "b", c: castling rights, last: [from, to]}
        return (name.charCodeAt(1) - 49) * 8 + (name.charCodeAt(0) - 97);
    }

    function parseFen(fen) {
        const parts = fen.split(" ");
        const b = new Array(64).fill(null);
        parts[0].split("/").forEach((row, i) => {
            let file = 0;
            for (const ch of row) {
                if (ch >= "1" && ch <= "8") {
                    file += +ch;
                } else {
                    b[(7 - i) * 8 + file++] = ch;
                }
            }
        });
        return {b: b, t: parts[1], c: parts[2] === "-" ? "" : parts[2], last: null};
    }

    function posKey(pos) {    // Transpositions reach the same position by different routes; used to merge them. En passant info is excluded
        return pos.b.map(p => p || ".").join("") + pos.t + pos.c;
    }

    const rightsLostAt = {0: "Q", 7: "K", 56: "q", 63: "k", 4: "KQ", 60: "kq"};

    function applyMove(pos, uci) {    // Moves are guaranteed legal by python-chess; this only applies them
        const from = sqIndex(uci.substr(0, 2));
        const to = sqIndex(uci.substr(2, 2));
        const promo = uci.charAt(4);
        const b = pos.b.slice();
        const piece = b[from];
        const white = piece === piece.toUpperCase();
        const kind = piece.toLowerCase();
        if (kind === "p" && from % 8 !== to % 8 && !b[to]) {
            b[to + (white ? -8 : 8)] = null;    // En passant
        }
        if (kind === "k" && Math.abs(to - from) === 2) {
            const rookFrom = to > from ? from + 3 : from - 4;
            b[(from + to) / 2] = b[rookFrom];    // Castling
            b[rookFrom] = null;
        }
        b[to] = promo ? (white ? promo.toUpperCase() : promo) : piece;
        b[from] = null;
        const lost = (rightsLostAt[from] || "") + (rightsLostAt[to] || "");
        const c = pos.c.split("").filter(ch => lost.indexOf(ch) < 0).join("");
        return {b: b, t: pos.t === "w" ? "b" : "w", c: c, last: [from, to]};
    }

    function lineStart(index) {
        return parseFen(data.l[index][0] || startFen);
    }

    function lineMoves(index) {
        return data.l[index][1].split(" ").filter(Boolean);
    }

    function buildGraph(indexes) {    // Position -> set of registered moves from that position
        const graph = new Map();
        for (const index of indexes) {
            let pos = lineStart(index);
            for (const uci of lineMoves(index)) {
                const key = posKey(pos);
                if (!graph.has(key)) {
                    graph.set(key, new Set());
                }
                graph.get(key).add(uci);
                pos = applyMove(pos, uci);
            }
        }
        return graph;
    }

    // ### Drawing ###

    const center = sq => {
        const col = flipped ? 7 - sq % 8 : sq % 8;
        const row = flipped ? Math.floor(sq / 8) : 7 - Math.floor(sq / 8);
        return [col * 100 + 50, row * 100 + 50];
    };

    function arrowSvg(from, to, cls) {
        const [x1, y1] = center(from);
        const [x2, y2] = center(to);
        const fileDiff = Math.abs(from % 8 - to % 8);
        const rankDiff = Math.abs(Math.floor(from / 8) - Math.floor(to / 8));
        let pts = [[x1, y1], [x2, y2]];
        if (fileDiff * rankDiff === 2) {    // Knight move (L-shape)
            pts = fileDiff > rankDiff ? [[x1, y1], [x2, y1], [x2, y2]] : [[x1, y1], [x1, y2], [x2, y2]];
        }
        const [px, py] = pts[pts.length - 2];
        const len = Math.hypot(x2 - px, y2 - py);
        const ux = (x2 - px) / len;
        const uy = (y2 - py) / len;
        const tip = [x2 - ux * 10, y2 - uy * 10];
        const base = [tip[0] - ux * 28, tip[1] - uy * 28];
        const line = pts.slice(0, -1).concat([base]).map(p => p.join(",")).join(" ");
        const head = [tip, [base[0] - uy * 21, base[1] + ux * 21], [base[0] + uy * 21, base[1] - ux * 21]].map(p => p.join(",")).join(" ");
        return `<g class="cb-ar ${'$'}{cls}"><polyline points="${'$'}{line}"/><polygon points="${'$'}{head}"/></g>`;
    }

    function createBoard(el) {
        const own = +el.dataset.own;
        const scope = el.dataset.scope === "all" ? data.l.map((_, i) => i) : [own];
        const graph = buildGraph(scope);
        const ownMoves = lineMoves(own);
        const ownStart = lineStart(own);
        const info = infoByIdx[own];
        const isAll = el.dataset.scope === "all";

        el.innerHTML = '<svg class="cb-svg" viewBox="0 0 800 800" role="img"></svg>' +
            '<div class="cb-ctl"><button type="button" class="cb-prev"></button><button type="button" class="cb-reset"></button><button type="button" class="cb-next"></button></div>';
        const svg = el.querySelector(".cb-svg");
        svg.setAttribute("aria-label", el.getAttribute("aria-label") || "");
        const prevBtn = el.querySelector(".cb-prev");
        const resetBtn = el.querySelector(".cb-reset");
        const nextBtn = el.querySelector(".cb-next");
        prevBtn.textContent = "◀ Prev";
        resetBtn.textContent = "↺ Reset";
        nextBtn.textContent = "Next ▶";

        let pos, hist, redo, sel, moves, movable, targets, down;

        // ### Matching Lines (starting-position board only) ###

        const cards = isAll ? [...document.querySelectorAll(".line-card[data-idx]")].map(c => +c.dataset.idx) : [];    // In page order, top to bottom
        const lineKeys = new Map();
        for (const index of cards) {
            let p = lineStart(index);
            const keys = new Set([posKey(p)]);
            for (const uci of lineMoves(index)) {
                p = applyMove(p, uci);
                keys.add(posKey(p));
            }
            lineKeys.set(index, keys);
        }
        const matchEl = document.createElement("div");
        matchEl.className = "cb-match";
        let defaultMatches = [];
        let showAllChips = false;    // Whether all chips are expanded when there are more than 4

        function matchesAt(p) {
            const key = posKey(p);
            return cards.filter(index => lineKeys.get(index).has(key));
        }

        function labelOf(index) {    // Variant › SubCategory #k; #k is omitted when the section has only one Line
            const card = document.getElementById("line-" + index);
            const parts = [card.closest(".variant").querySelector(".variant-title").textContent.trim()];
            const sub = card.closest(".subcategory");
            if (sub) {
                parts.push(sub.querySelector(".subcategory-title").textContent.trim());
            }
            const siblings = [...card.parentElement.children].filter(c => c.classList.contains("line-card"));
            return parts.map(part => part || "—").join(" › ") + (siblings.length > 1 ? " #" + (siblings.indexOf(card) + 1) : "");
        }

        function jumpTo(index) {
            const card = document.getElementById("line-" + index);
            card.open = true;
            card.classList.remove("cb-flash");
            void card.offsetWidth;    // Retrigger the flash animation
            card.classList.add("cb-flash");
            const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
            card.scrollIntoView({behavior: reduceMotion ? "auto" : "smooth", block: "start"});
        }

        function makeChip(index) {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "cb-chip";
            chip.textContent = labelOf(index);
            chip.addEventListener("click", () => jumpTo(index));
            return chip;
        }

        function makeToggle(text, expand) {
            const toggle = document.createElement("button");
            toggle.type = "button";
            toggle.className = "cb-toggle";
            toggle.textContent = text;
            toggle.setAttribute("aria-expanded", expand ? "false" : "true");
            toggle.addEventListener("click", () => {
                showAllChips = expand;
                renderMatches();
                matchEl.querySelector(".cb-toggle").focus({preventScroll: true});
            });
            return toggle;
        }

        function renderMatches() {
            matchEl.textContent = "";
            const matched = matchesAt(pos);
""",
    """            if (!matched.length || defaultMatches.every(index => matched.includes(index))) {
                showAllChips = false;
                return;    // Not narrower than the default position, so matching is pointless
            }
            const overflow = matched.length > 4;
            if (!overflow) {
                showAllChips = false;
            }
            for (const index of overflow && !showAllChips ? matched.slice(0, 3) : matched) {
                matchEl.appendChild(makeChip(index));
            }
            if (overflow && !showAllChips) {
                matchEl.appendChild(makeToggle(data.t.viewAll.replace("{n}", matched.length), true));    // 4th slot
            } else if (overflow) {
                const foot = document.createElement("div");
                foot.className = "cb-foot";
                foot.appendChild(makeToggle(data.t.collapse, false));    // Bottom of the expanded list
                matchEl.appendChild(foot);
            }
        }

        function updateMark() {    // Mark the current move in the PGN text; no mark when off the own PGN path or inside the trimmed range
            if (!info || !info.valid) {
                return;
            }
            if (info.cur) {
                info.cur.classList.remove("cur");
                info.cur = null;
            }
            const span = onOwnPath() && hist.length ? info.spans[hist.length - 1 - info.base] : null;
            if (span) {
                span.classList.add("cur");
                info.cur = span;
            }
        }

        function onOwnPath() {
            return hist.length <= ownMoves.length && hist.every((h, i) => h.uci === ownMoves[i]);
        }

        function ownNext() {    // Next PGN move while still on the own PGN path
            return onOwnPath() && hist.length < ownMoves.length ? ownMoves[hist.length] : null;
        }

        function nextMove() {
            if (ownNext()) {
                return ownNext();
            }
            return redo.length ? redo[redo.length - 1] : null;
        }

        function play(uci) {
            if (redo.length && redo[redo.length - 1] === uci) {
                redo.pop();
            } else {
                redo = [];
            }
            hist.push({uci: uci, prev: pos});
            pos = applyMove(pos, uci);
            sel = null;
            refresh();
        }

        function goPrev() {
            if (!hist.length) {
                return;
            }
            const h = hist.pop();
            redo.push(h.uci);
            pos = h.prev;
            sel = null;
            refresh();
        }

        function goNext() {
            const uci = nextMove();
            if (uci) {
                play(uci);
            }
        }

        function goTo(ply) {    // Jump to just after ply N of the own PGN
            pos = ownStart;
            hist = [];
            redo = [];
            sel = null;
            for (const uci of ownMoves.slice(0, ply)) {
                hist.push({uci: uci, prev: pos});
                pos = applyMove(pos, uci);
            }
            refresh();
        }

        function reset() {    // Back to the final PGN position
            goTo(ownMoves.length);
        }

        function tryMove(from, to) {
            const options = [...moves].filter(u => sqIndex(u.substr(0, 2)) === from && sqIndex(u.substr(2, 2)) === to);
            if (!options.length) {
                return;
            }
            play(options.find(u => u.charAt(4) === "q") || options[0]);    // Prefer queen when several promotions go to the same square
        }

        function refresh() {
            moves = graph.get(posKey(pos)) || new Set();
            movable = new Set([...moves].map(u => sqIndex(u.substr(0, 2))));
            targets = new Set([...moves].filter(u => sqIndex(u.substr(0, 2)) === sel).map(u => sqIndex(u.substr(2, 2))));
            renderBoard();
            updateMark();
            if (isAll) {
                renderMatches();
            }
            prevBtn.disabled = !hist.length;
            nextBtn.disabled = !nextMove();
            resetBtn.disabled = hist.length === ownMoves.length && onOwnPath();
        }

        function renderBoard() {
            let s = "";
            for (let sq = 0; sq < 64; sq++) {
                const [cx, cy] = center(sq);
                const x = cx - 50;
                const y = cy - 50;
                const dark = (sq % 8 + Math.floor(sq / 8)) % 2 === 0;
                s += `<rect x="${'$'}{x}" y="${'$'}{y}" width="100" height="100" class="${'$'}{dark ? "cb-sq-d" : "cb-sq-l"}"/>`;
                if (pos.last && pos.last.indexOf(sq) >= 0) {
                    s += `<rect x="${'$'}{x}" y="${'$'}{y}" width="100" height="100" class="cb-last"/>`;
                }
                if (sq === sel) {
                    s += `<rect x="${'$'}{x}" y="${'$'}{y}" width="100" height="100" class="cb-sel"/>`;
                }
                const coCls = dark ? "cb-co-d" : "cb-co-l";
                if (x === 0) {
                    s += `<text x="${'$'}{x + 6}" y="${'$'}{y + 24}" class="cb-co ${'$'}{coCls}">${'$'}{Math.floor(sq / 8) + 1}</text>`;
                }
                if (y === 700) {
                    s += `<text x="${'$'}{x + 94}" y="${'$'}{y + 92}" text-anchor="end" class="cb-co ${'$'}{coCls}">${'$'}{"abcdefgh"[sq % 8]}</text>`;
                }
            }
            for (const sq of targets) {
                const [cx, cy] = center(sq);
                s += pos.b[sq] ? `<circle cx="${'$'}{cx}" cy="${'$'}{cy}" r="42" class="cb-ring"/>` : `<circle cx="${'$'}{cx}" cy="${'$'}{cy}" r="16" class="cb-dot"/>`;
            }
            for (let sq = 0; sq < 64; sq++) {
                if (pos.b[sq]) {
                    const [cx, cy] = center(sq);
                    s += `<use href="#pc-${'$'}{pos.b[sq]}" x="${'$'}{cx - 50}" y="${'$'}{cy - 50}" width="100" height="100" class="cb-pc" data-sq="${'$'}{sq}"/>`;
                }
            }
            const main = ownNext();
            const drawn = new Set();
            for (const uci of moves) {
                const from = sqIndex(uci.substr(0, 2));
                const to = sqIndex(uci.substr(2, 2));
                const id = from + "-" + to;
                if (!drawn.has(id)) {
                    drawn.add(id);
                    s += arrowSvg(from, to, main && main.substr(0, 4) === uci.substr(0, 4) ? "cb-ar-main" : "cb-ar-alt");
                }
            }
            svg.innerHTML = s;
        }

        // ### Click and drag ###

        function squareAt(clientX, clientY) {
            const rect = svg.getBoundingClientRect();
            const x = (clientX - rect.left) / rect.width * 8;
            const y = (clientY - rect.top) / rect.height * 8;
            if (x < 0 || x >= 8 || y < 0 || y >= 8) {
                return -1;
            }
            const col = Math.floor(x);
            const row = Math.floor(y);
            return (flipped ? row : 7 - row) * 8 + (flipped ? 7 - col : col);
        }

        function toSvgPoint(clientX, clientY) {
            const rect = svg.getBoundingClientRect();
            return [(clientX - rect.left) / rect.width * 800, (clientY - rect.top) / rect.height * 800];
        }

        function startDrag() {
            down.dragging = true;
            const ghost = svg.querySelector(`.cb-pc[data-sq="${'$'}{down.sq}"]`);
            ghost.classList.add("cb-ghost");
            down.floater = ghost.cloneNode();
            down.floater.removeAttribute("data-sq");
            down.floater.setAttribute("class", "cb-float");
            svg.appendChild(down.floater);
        }

        svg.addEventListener("pointerdown", e => {
            if (e.pointerType === "mouse" && e.button !== 0) {
                return;
            }
            const sq = squareAt(e.clientX, e.clientY);
            if (sq < 0) {
                return;
            }
            svg.setPointerCapture(e.pointerId);
            down = {sq: sq, id: e.pointerId, x: e.clientX, y: e.clientY, fromPiece: movable.has(sq), wasSelected: sel === sq, dragging: false};
            if (down.fromPiece) {
                sel = sq;
                refresh();
            }
        });

        svg.addEventListener("pointermove", e => {
            if (!down) {
                svg.style.cursor = movable.has(squareAt(e.clientX, e.clientY)) ? "grab" : "default";
                return;
            }
            if (!down.fromPiece || e.pointerId !== down.id) {
                return;
            }
            if (!down.dragging) {
                if (Math.hypot(e.clientX - down.x, e.clientY - down.y) < 6) {
                    return;    // Movement too small counts as a click
                }
                startDrag();
            }
            const [px, py] = toSvgPoint(e.clientX, e.clientY);
            down.floater.setAttribute("x", px - 50);
            down.floater.setAttribute("y", py - 50);
        });

        svg.addEventListener("pointerup", e => {
            if (!down || e.pointerId !== down.id) {
                return;
            }
            const d = down;
            down = null;
            const sq = squareAt(e.clientX, e.clientY);
            if (d.dragging) {
                if (sq >= 0 && targets.has(sq)) {
                    tryMove(d.sq, sq);
                } else {
                    refresh();    // Dropped on a square with no registered move: piece snaps back
                }
            } else if (d.fromPiece) {
                if (d.wasSelected) {
                    sel = null;    // Clicking the selected piece again deselects it
                }
                refresh();
            } else if (sel !== null && sq >= 0 && targets.has(sq)) {
                tryMove(sel, sq);
            } else {
                sel = null;
                refresh();
            }
        });

        svg.addEventListener("pointercancel", () => {
            down = null;
            refresh();
        });

        svg.addEventListener("touchstart", e => {    // Only movable pieces block scrolling; the rest of the board still scrolls the page
            const t = e.touches[0];
            if (movable.has(squareAt(t.clientX, t.clientY))) {
                e.preventDefault();
            }
        }, {passive: false});

        prevBtn.addEventListener("click", goPrev);
        nextBtn.addEventListener("click", goNext);
        resetBtn.addEventListener("click", reset);

        if (isAll) {
            el.appendChild(matchEl);
            let endPos = ownStart;
            for (const uci of ownMoves) {
                endPos = applyMove(endPos, uci);
            }
            defaultMatches = matchesAt(endPos);
        }
        if (info && info.valid) {
            info.spans.forEach(span => span.classList.add("live"));
            info.container.addEventListener("click", e => {    // Clicking a move in the PGN jumps the board to it
                const span = e.target.closest(".pgn-mv");
                if (span) {
                    e.preventDefault();    // Prevent the click from also collapsing the row
                    goTo(info.base + (+span.dataset.j) + 1);
                }
            });
        }

        reset();
        boards.push(reset);
    }

    preparePgn();

    document.querySelectorAll(".cb").forEach(el => {
        const card = el.closest("details");
        if (!card || card.open) {
            createBoard(el);
            return;
        }
        const initOnce = () => {    // Draw only when the Line card is expanded
            card.removeEventListener("toggle", initOnce);
            if (!el.childElementCount) {
                createBoard(el);
            }
        };
        card.addEventListener("toggle", initOnce);
        pendingInits.push(initOnce);
    });

    let fitQueued = false;
    const queueFit = () => {
        if (!fitQueued) {
            fitQueued = true;
            requestAnimationFrame(() => {
                fitQueued = false;
                fitCollapsed();
            });
        }
    };
    fitCollapsed();
    window.addEventListener("resize", queueFit);
    document.addEventListener("toggle", queueFit, true);    // toggle doesn't bubble; capture it; recompute on collapse
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(queueFit);
    }

    window.addEventListener("beforeprint", () => {    // On print, every board returns to the default position
        pendingInits.forEach(fn => fn());
        boards.forEach(reset => reset());
    });
})();
"""
).joinToString("")
