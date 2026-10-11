"""CampusAI - all AI algorithms (pure Python, no ML libraries)."""
import heapq, itertools, math, random
from collections import Counter, defaultdict

# ---------- seed data ----------
FOODS = [("Paneer Sandwich","Snack","Paneer,Bread",1,0),("Veg Pasta","Main","Pasta,Vegetables",1,1),
 ("Margherita Pizza","Main","Cheese,Bread,Tomato",1,0),("Peanut Chaat","Snack","Peanut,Onion",1,2),
 ("Chicken Burger","Main","Chicken,Bread",0,1),("Egg Fried Rice","Main","Egg,Rice",0,1),
 ("Veg Biryani","Main","Rice,Vegetables,Spices",1,2),("Fruit Salad","Dessert","Fruits",1,0),
 ("Peanut Butter Toast","Snack","Peanut,Bread",1,0),("Fish Curry Meal","Main","Fish,Rice",0,2)]
_r = random.Random(1); _base = [120,135,128,150,160,90,70]
HISTORY = [(_base[i % 7] + (i // 7) * 3 + _r.randint(-6, 6), round(_r.uniform(5, 20), 1)) for i in range(28)]
DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

# ---------- Exp 2: rule-based food recommendation ----------
SP = {"Low": 0, "Medium": 1, "High": 2}
def food(d, c):
    avoid = d.get("avoid", "").strip().lower(); veg = d["diet"] == "Vegetarian"; mx = SP[d["spice"]]
    ok = [r["name"] for r in c.execute("select * from food_items")
          if (r["veg"] or not veg) and r["spicy"] <= mx and not (avoid and avoid in r["ingredients"].lower())]
    return {"recommended": ok or ["No matching food"], "rule": "suitable(F) :- diet_ok(F), spice(F) <= pref, not contains(F, avoid)"}

# ---------- Exp 1: delivery planning (Dijkstra over campus graph) ----------
EDGES = [("Warehouse","W1",.5),("Warehouse","W2",.7),("W1","W3",.6),("W2","W3",.4),("W1","W2",.3),
         ("W3","Building C",.7),("W2","Building C",1.1),("Warehouse","W3",1.4)]
def delivery(d, c):
    s, g = d["start"], d["goal"]; allowed = {s, g, *[w.strip() for w in d["waypoints"].split(",") if w.strip()]}
    adj = defaultdict(list)
    for a, b, w in EDGES:
        if a in allowed and b in allowed: adj[a].append((b, w)); adj[b].append((a, w))
    pq, seen = [(0, s, [s])], set()
    while pq:
        dist, n, path = heapq.heappop(pq)
        if n == g: return {"route": " -> ".join(path), "distance_km": round(dist, 2), "energy_units": round(dist * 13.3, 1)}
        if n in seen: continue
        seen.add(n)
        for m, w in adj[n]: heapq.heappush(pq, (dist + w, m, path + [m]))
    return {"route": "No route with these waypoints"}

# ---------- Exp 4: A* grid navigation ----------
def astar(d, c):
    grid = d["grid"]; R, C = len(grid), len(grid[0])
    pos = {ch: (r, k) for r, row in enumerate(grid) for k, ch in enumerate(row) if ch in "SG"}
    s, g = pos["S"], pos["G"]; h = lambda p: abs(p[0]-g[0]) + abs(p[1]-g[1])
    pq, best, prev = [(h(s), 0, s)], {s: 0}, {}
    while pq:
        _, cost, n = heapq.heappop(pq)
        if n == g:
            path = [n]
            while n in prev: n = prev[n]; path.append(n)
            path.reverse(); return {"path": path, "path_length_cells": len(path), "cost": cost}
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            m = (n[0]+dr, n[1]+dc)
            if 0 <= m[0] < R and 0 <= m[1] < C and grid[m[0]][m[1]] != "X" and cost + 1 < best.get(m, 1e9):
                best[m] = cost + 1; prev[m] = n; heapq.heappush(pq, (cost + 1 + h(m), cost + 1, m))
    return {"path": [], "message": "No path - goal is blocked"}

# ---------- Break-Time Planner (minimax) ----------
# option: (eating-time factor, wait normal, wait rush, wait sold-out, penalty for a lighter meal)
OPTIONS = {"Dine-in meal": (1.0, 4, 12, 8, 0), "Takeaway meal": (.6, 5, 10, 8, 2), "Quick snack counter": (.3, 2, 5, 10, 6)}
def breakplanner(d, c):
    base = d["break_min"] - 2 * d["walk_main"]; rows = []
    for name, (f, w1, w2, w3, pen) in OPTIONS.items():
        left = base - d["eat_min"] * f
        sc = {"normal_queue": round(left - w1), "rush_hour": round(left - w2), "item_sold_out": round(left - w3)}
        worst = min(sc.values())                                   # MIN over scenarios
        rows.append(({"option": name, **sc, "worst_case": worst}, min(worst, 10) - pen))
    best = max(rows, key=lambda t: t[1])[0]                        # MAX over options
    adv = "You will be back on time even in the worst case." if best["worst_case"] >= 0 else "Even the safest option may make you late - take a packed snack."
    return {"recommended_option": best["option"], "guaranteed_spare_minutes": best["worst_case"], "advice": adv,
            "spare_minutes_by_scenario": [t[0] for t in rows],
            "rule": "Minimax: choose the option whose worst-case spare time (capped at 10 min, minus a small penalty for lighter meals) is highest"}

# ---------- Exp 6 & 7: fuzzy inference (zero-order Sugeno, 27 rules) ----------
LV = ["Very Low", "Low", "Medium", "High", "Very High"]
def _fz(x):
    x = max(0, min(1, x)); return [max(0, (.5 - x) / .5), 1 - abs(x - .5) / .5, max(0, (x - .5) / .5)]
def infer(vals, inv=()):
    ms = [_fz(v) for v in vals]
    for i in inv: ms[i] = ms[i][::-1]
    num = den = 0
    for idx in itertools.product(range(3), repeat=len(ms)):      # rule = (Low/Med/High)^n
        w = min(ms[k][i] for k, i in enumerate(idx))             # AND = min
        num += w * sum(idx) / (2 * len(idx)) * 100; den += w     # consequent, weighted average
    s = round(num / den, 1); return {"score": s, "level": LV[min(4, int(s // 20))]}
def mealtime(h): return max(math.exp(-((h-12.5)/1.5)**2), .7*math.exp(-((h-19.5)/1.5)**2), .5*math.exp(-((h-8.5)/1)**2))
def queue(d, c):
    r = infer([d["queue"]/60, d["counters"]/6, d["minutes"]/60], inv=(0,))   # long queue = bad, open counters + spare time = good
    wait = round(d["queue"] / max(1, d["counters"]) * 1.2)
    note = "You may miss your next class if you queue now." if wait > d["minutes"] else "You can finish before your next class."
    return {"advice": ["Skip it", "Wait a bit", "Borderline", "Good to go", "Go now"][min(4, int(r["score"] // 20))],
            "go_score": r["score"], "estimated_wait_min": wait, "note": note}
def foodprep(d, c):
    r = infer([d["demand"]/200, d["remaining"]/100, mealtime(d["hour"])], inv=(1,))
    return {"preparation_level": r["level"], "score": r["score"]}

# ---------- Exp 8: neuro-fuzzy (tiny MLP demand predictor -> fuzzy decision) ----------
def _train(rows):
    r = random.Random(0); H, n = 6, 8
    W1 = [[r.uniform(-.5, .5) for _ in range(n)] for _ in range(H)]; b1 = [0]*H
    W2 = [r.uniform(-.5, .5) for _ in range(H)]; b2 = [0]
    feat = lambda day, prev: [1.0 if i == day else 0.0 for i in range(7)] + [prev / 200]
    def fwd(x):
        h = [math.tanh(sum(w*v for w, v in zip(W1[j], x)) + b1[j]) for j in range(H)]
        return h, sum(a*b for a, b in zip(W2, h)) + b2[0]
    data = [(feat(rows[i][0], rows[i-1][1]), rows[i][1] / 200) for i in range(1, len(rows))]
    for _ in range(700):
        for x, t in data:
            h, y = fwd(x); e = y - t
            for j in range(H):
                g = e * W2[j] * (1 - h[j]**2); W2[j] -= .05 * e * h[j]
                for k in range(n): W1[j][k] -= .05 * g * x[k]
                b1[j] -= .05 * g
            b2[0] -= .05 * e
    mae = sum(abs(fwd(x)[1] - t) for x, t in data) / len(data) * 200
    return (lambda day, prev: fwd(feat(day, prev))[1] * 200), mae
def neurofuzzy(d, c):
    rows = [(r["day"], r["demand"]) for r in c.execute("select day, demand from cafeteria_data order by id")]
    predict, mae = _train(rows); pred = predict(DAYS.index(d["day"]), d["prev_demand"])
    r = infer([pred/200, d["remaining"]/100, mealtime(d["hour"])], inv=(1,))
    return {"predicted_demand_meals": round(pred), "training_MAE_meals": round(mae, 1),
            "preparation_level": r["level"], "score": r["score"]}

# ---------- Exp 9: Best Time to Eat = perceptron (supervised) + competitive learning (unsupervised) ----------
def _data():
    r = random.Random(2); X, Y = [], []
    for _ in range(60):
        x = [r.uniform(50, 250)/250, r.uniform(40, 250)/250, r.uniform(0, 40)/40]
        X.append(x); Y.append(1 if 1.2*(x[0]-x[1]) + x[2] > .6 else 0)
    return X, Y
def _perceptron():                       # learns High/Low food-wastage risk from planned, customers, leftover
    X, Y = _data(); w, b = [0.0]*3, 0.0
    for _ in range(200):
        for x, y in zip(X, Y):
            e = y - (1 if sum(a*v for a, v in zip(w, x)) + b > 0 else 0)
            w = [a + .1*e*v for a, v in zip(w, x)]; b += .1*e
    f = lambda x: 1 if sum(a*v for a, v in zip(w, x)) + b > 0 else 0
    return f, w, b, sum(f(x) == y for x, y in zip(X, Y)) / len(X)
def _cluster(X):                         # winner-take-all competitive learning, 3 neurons
    r = random.Random(5); cent = [list(p) for p in r.sample(X, 3)]
    win = lambda x: min(range(3), key=lambda k: sum((a-b)**2 for a, b in zip(cent[k], x)))
    for ep in range(60):
        lr = .2 * (1 - ep/60)
        for x in X:
            k = win(x); cent[k] = [a + lr*(v-a) for a, v in zip(cent[k], x)]
    return cent, win
def _slots():                            # half-hour slot history: (hour, planned, customers, leftover %)
    r = random.Random(3); S = []
    for i in range(30):
        h = 7 + i * .5; cu = min(250, round(30 + 190*mealtime(h) + r.randint(-8, 8)))
        pl = min(250, round(cu * r.uniform(.85, 1.5))); lo = min(40, max(0, round((pl-cu)/pl*40 + r.uniform(0, 6))))
        S.append((h, pl, cu, lo))
    return S
_tl = lambda h: f"{int(h) % 12 or 12}:{'30' if h % 1 else '00'} {'AM' if h < 12 else 'PM'}"
MEALS = {"Breakfast": (7, 10), "Lunch": (11, 15), "Snacks": (16, 18.5), "Dinner": (19, 22)}
def mealplanner(d, c):
    lo, hi = MEALS[d["meal"]]; f, w, b, acc = _perceptron(); S = _slots()
    X = [[p/250, q/250, l/40] for _, p, q, l in S]; cent, win = _cluster(X)
    order = sorted(range(3), key=lambda k: cent[k][1]); name = {order[0]: "Quiet", order[1]: "Moderate", order[2]: "Rush"}
    rows = []
    for (h, p, q, l), x in zip(S, X):
        if lo <= h <= hi:
            plenty = f(x) == 1
            score = -q if d["priority"].startswith("Avoid") else (1000 if plenty else 0) - q
            rows.append((score, {"time": _tl(h), "crowd": name[win(x)], "wait_min": max(1, round(q/18)), "food": "Plentiful" if plenty else "Limited"}))
    best = max(rows, key=lambda t: t[0])[1]
    return {"best_time": best["time"], "why": f"{best['crowd']} crowd, about {best['wait_min']} min wait, food {best['food'].lower()}",
            "slots": [t[1] for t in rows],
            "model": {"perceptron_accuracy": f"{acc:.0%}", "weights": [round(a, 2) for a in w],
                      "cluster_centres_customers": {name[k]: round(cent[k][1]*250) for k in order}}}

# ---------- Exp 10: micro (bigram) and small (trigram + backoff) language models ----------
CORPUS = ["the cafeteria serves fresh vegetarian meals at lunch","the cafeteria prepares more food when demand is high",
 "fuzzy logic decides the food preparation level","the neural network predicts the expected demand for lunch",
 "the waste bin needs urgent collection when it is full","the cafeteria reduces food waste with smart planning",
 "students prefer low spicy vegetarian meals at lunch","the cafeteria prepares less food when demand is low",
 "the smart cafeteria predicts demand for the next day","the waste collection priority is very high when the bin is full",
 "the cafeteria serves hot meals at dinner","fresh meals are prepared when the remaining food is low"]
def _ngrams(n):
    m = defaultdict(Counter)
    for s in CORPUS:
        t = s.split()
        for i in range(len(t) - n + 1): m[tuple(t[i:i+n-1])][t[i+n-1]] += 1
    return m
_BI, _TRI, _UNI = _ngrams(2), _ngrams(3), Counter(w for s in CORPUS for w in s.split())
def _next(toks, small):
    for ctx, tab in ((tuple(toks[-2:]), _TRI),) * small + ((tuple(toks[-1:]), _BI),):
        if ctx in tab and len(ctx) == (2 if tab is _TRI else 1): return tab[ctx]
    return _UNI
def slm(d, c):
    small = d["model"].startswith("Small"); toks = d["text"].lower().split()
    cnt = _next(toks, small); tot = sum(cnt.values())
    top = {w: round(v/tot, 2) for w, v in cnt.most_common(3)}
    out = list(toks)
    for _ in range(int(d["words"])):
        cn = _next(out, small); out.append(random.choices(list(cn), list(cn.values()))[0])
    return {"model": "SLM (trigram + backoff)" if small else "uLM (bigram)", "next_word_predictions": top, "generated_text": " ".join(out)}

RUN = {"food": food, "delivery": delivery, "astar": astar, "breakplanner": breakplanner, "queue": queue, "foodprep": foodprep,
       "neurofuzzy": neurofuzzy, "mealplanner": mealplanner, "slm": slm}
