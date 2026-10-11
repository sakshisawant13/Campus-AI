import json, sqlite3
from flask import Flask, request, jsonify, render_template
import algorithms as A

app = Flask(__name__); DB = "database.db"
def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c
def init():
    c = db()
    c.executescript("""CREATE TABLE IF NOT EXISTS food_items(id INTEGER PRIMARY KEY, name, category, ingredients, veg INT, spicy INT);
    CREATE TABLE IF NOT EXISTS cafeteria_data(id INTEGER PRIMARY KEY, day INT, demand INT, waste REAL);
    CREATE TABLE IF NOT EXISTS ai_history(id INTEGER PRIMARY KEY, module, input_data, output, ts DEFAULT CURRENT_TIMESTAMP);""")
    if not c.execute("select count(*) from food_items").fetchone()[0]:
        c.executemany("insert into food_items(name,category,ingredients,veg,spicy) values(?,?,?,?,?)", A.FOODS)
        c.executemany("insert into cafeteria_data(day,demand,waste) values(?,?,?)", [(i % 7, d, w) for i, (d, w) in enumerate(A.HISTORY)])
    c.commit(); c.close()

@app.get("/")
def home(): return render_template("index.html")

@app.post("/api/<mod>")
def run(mod):
    if mod not in A.RUN: return jsonify(error="unknown module"), 404
    data = request.get_json(force=True); c = db()
    try: res = A.RUN[mod](data, c)
    except Exception as e: return jsonify(error=f"Invalid input: {e}"), 400
    c.execute("insert into ai_history(module,input_data,output) values(?,?,?)", (mod, json.dumps(data)[:300], json.dumps(res)[:300]))
    c.commit(); c.close(); return jsonify(res)

@app.get("/api/history")
def history():
    c = db(); rows = [dict(r) for r in c.execute("select * from ai_history order by id desc limit 50")]; c.close(); return jsonify(rows)

@app.post("/api/history/delete")
def hist_delete():
    ids = request.get_json(force=True).get("ids", []); c = db()
    c.executemany("delete from ai_history where id=?", [(int(i),) for i in ids]); c.commit(); c.close()
    return jsonify(deleted=len(ids))

@app.get("/api/stats")
def stats():
    c = db(); r = {x["module"]: x["n"] for x in c.execute("select module, count(*) n from ai_history group by module")}
    r["_total"] = sum(r.values()); r["_foods"] = c.execute("select count(*) from food_items").fetchone()[0]
    r["_days"] = c.execute("select count(*) from cafeteria_data").fetchone()[0]; c.close(); return jsonify(r)

init()
if __name__ == "__main__": app.run(debug=True)
