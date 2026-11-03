(function () {
    const data = JSON.parse(document.getElementById("boardData").textContent);
    const startFen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
    const flipped = data.o === "black";
    const boards = [];    // 已建立的棋盤，列印前統一重置
    const pendingInits = [];    // 尚未展開的 Line 卡片，列印前一併建立

    // ### 局面與走子 ###
    // 局面格式：{b: 64 格陣列（a1 = 0，h8 = 63）, t: "w" | "b", c: 王車易位權利, last: [起點, 終點]}

    function sqIndex(name) {
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

    function posKey(pos) {    // 換位時不同路線會走到同一局面，以此合併；不含吃過路兵資訊
        return pos.b.map(p => p || ".").join("") + pos.t + pos.c;
    }

    const rightsLostAt = {0: "Q", 7: "K", 56: "q", 63: "k", 4: "KQ", 60: "kq"};

    function applyMove(pos, uci) {    // 著法由 python-chess 保證合法，這裡只負責套用
        const from = sqIndex(uci.substr(0, 2));
        const to = sqIndex(uci.substr(2, 2));
        const promo = uci.charAt(4);
        const b = pos.b.slice();
        const piece = b[from];
        const white = piece === piece.toUpperCase();
        const kind = piece.toLowerCase();
        if (kind === "p" && from % 8 !== to % 8 && !b[to]) {
            b[to + (white ? -8 : 8)] = null;    // 吃過路兵
        }
        if (kind === "k" && Math.abs(to - from) === 2) {
            const rookFrom = to > from ? from + 3 : from - 4;
            b[(from + to) / 2] = b[rookFrom];    // 王車易位
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

    function buildGraph(indexes) {    // 局面 → 該局面下已登錄的著法集合
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

    // ### 繪圖 ###

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
        if (fileDiff * rankDiff === 2) {    // 馬走 L 形
            pts = fileDiff > rankDiff ? [[x1, y1], [x2, y1], [x2, y2]] : [[x1, y1], [x1, y2], [x2, y2]];
        }
        const [px, py] = pts[pts.length - 2];
        const len = Math.hypot(x2 - px, y2 - py);
        const ux = (x2 - px) / len;
        const uy = (y2 - py) / len;
        const tip = [x2 - ux * 12, y2 - uy * 12];
        const base = [tip[0] - ux * 40, tip[1] - uy * 40];
        const line = pts.slice(0, -1).concat([base]).map(p => p.join(",")).join(" ");
        const head = [tip, [base[0] - uy * 30, base[1] + ux * 30], [base[0] + uy * 30, base[1] - ux * 30]].map(p => p.join(",")).join(" ");
        return `<g class="cb-ar ${cls}"><polyline points="${line}"/><polygon points="${head}"/></g>`;
    }

    function createBoard(el) {
        const own = +el.dataset.own;
        const scope = el.dataset.scope === "all" ? data.l.map((_, i) => i) : [own];
        const graph = buildGraph(scope);
        const ownMoves = lineMoves(own);
        const ownStart = lineStart(own);

        el.innerHTML = '<svg class="cb-svg" viewBox="0 0 800 800" role="img"></svg>' +
            '<div class="cb-ctl"><button type="button" class="cb-prev"></button><button type="button" class="cb-reset"></button><button type="button" class="cb-next"></button></div>';
        const svg = el.querySelector(".cb-svg");
        svg.setAttribute("aria-label", el.getAttribute("aria-label") || "");
        const prevBtn = el.querySelector(".cb-prev");
        const resetBtn = el.querySelector(".cb-reset");
        const nextBtn = el.querySelector(".cb-next");
        prevBtn.textContent = "◀ " + data.t.prev;
        resetBtn.textContent = "↺ " + data.t.reset;
        nextBtn.textContent = data.t.next + " ▶";

        let pos, hist, redo, sel, moves, movable, targets, down;

        function onOwnPath() {
            return hist.length <= ownMoves.length && hist.every((h, i) => h.uci === ownMoves[i]);
        }

        function ownNext() {    // 目前仍在自己的 PGN 路徑上時，PGN 的下一步
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

        function reset() {    // 回到 PGN 最終局面
            pos = ownStart;
            hist = [];
            redo = [];
            sel = null;
            for (const uci of ownMoves) {
                hist.push({uci: uci, prev: pos});
                pos = applyMove(pos, uci);
            }
            refresh();
        }

        function tryMove(from, to) {
            const options = [...moves].filter(u => sqIndex(u.substr(0, 2)) === from && sqIndex(u.substr(2, 2)) === to);
            if (!options.length) {
                return;
            }
            play(options.find(u => u.charAt(4) === "q") || options[0]);    // 同格多種升變時優先皇后
        }

        function refresh() {
            moves = graph.get(posKey(pos)) || new Set();
            movable = new Set([...moves].map(u => sqIndex(u.substr(0, 2))));
            targets = new Set([...moves].filter(u => sqIndex(u.substr(0, 2)) === sel).map(u => sqIndex(u.substr(2, 2))));
            renderBoard();
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
                s += `<rect x="${x}" y="${y}" width="100" height="100" class="${dark ? "cb-sq-d" : "cb-sq-l"}"/>`;
                if (pos.last && pos.last.indexOf(sq) >= 0) {
                    s += `<rect x="${x}" y="${y}" width="100" height="100" class="cb-last"/>`;
                }
                if (sq === sel) {
                    s += `<rect x="${x}" y="${y}" width="100" height="100" class="cb-sel"/>`;
                }
                const coCls = dark ? "cb-co-d" : "cb-co-l";
                if (x === 0) {
                    s += `<text x="${x + 6}" y="${y + 24}" class="cb-co ${coCls}">${Math.floor(sq / 8) + 1}</text>`;
                }
                if (y === 700) {
                    s += `<text x="${x + 94}" y="${y + 92}" text-anchor="end" class="cb-co ${coCls}">${"abcdefgh"[sq % 8]}</text>`;
                }
            }
            for (const sq of targets) {
                const [cx, cy] = center(sq);
                s += pos.b[sq] ? `<circle cx="${cx}" cy="${cy}" r="42" class="cb-ring"/>` : `<circle cx="${cx}" cy="${cy}" r="16" class="cb-dot"/>`;
            }
            for (let sq = 0; sq < 64; sq++) {
                if (pos.b[sq]) {
                    const [cx, cy] = center(sq);
                    s += `<use href="#pc-${pos.b[sq]}" x="${cx - 50}" y="${cy - 50}" width="100" height="100" class="cb-pc" data-sq="${sq}"/>`;
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

        // ### 點擊與拖曳 ###

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
            const ghost = svg.querySelector(`.cb-pc[data-sq="${down.sq}"]`);
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
                    return;    // 位移太小視為點擊
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
                    refresh();    // 放到非登錄走法的格子，棋子彈回
                }
            } else if (d.fromPiece) {
                if (d.wasSelected) {
                    sel = null;    // 再點一次已選取的棋子 = 取消選取
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

        svg.addEventListener("touchstart", e => {    // 只有可走的棋子禁止捲動，棋盤其他地方仍可滑動捲頁
            const t = e.touches[0];
            if (movable.has(squareAt(t.clientX, t.clientY))) {
                e.preventDefault();
            }
        }, {passive: false});

        prevBtn.addEventListener("click", goPrev);
        nextBtn.addEventListener("click", goNext);
        resetBtn.addEventListener("click", reset);

        reset();
        boards.push(reset);
    }

    document.querySelectorAll(".cb").forEach(el => {
        const card = el.closest("details");
        if (!card || card.open) {
            createBoard(el);
            return;
        }
        const initOnce = () => {    // Line 卡片展開時才繪製
            card.removeEventListener("toggle", initOnce);
            if (!el.childElementCount) {
                createBoard(el);
            }
        };
        card.addEventListener("toggle", initOnce);
        pendingInits.push(initOnce);
    });

    window.addEventListener("beforeprint", () => {    // 列印時每個棋盤都回到預設局面
        pendingInits.forEach(fn => fn());
        boards.forEach(reset => reset());
    });
})();
