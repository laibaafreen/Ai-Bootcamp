"""
To-Do List REST API — FLASK version
Assignment: W2D4

Same logic as the FastAPI version, different syntax.
Run with:  python app.py
Then open: http://127.0.0.1:5000/todos  (Flask has NO built-in Swagger,
so we test with Postman, or install flask-swagger-ui separately)
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------
# Our "database" — a plain Python list, just like the FastAPI version
# ---------------------------------------------------------
todos = []
next_id = 1


# ---------------------------------------------------------
# Question 1: Add a new task
# ---------------------------------------------------------
@app.route("/todos", methods=["POST"])
def create_todo():
    global next_id

    data = request.get_json()  # Flask doesn't auto-validate like FastAPI —
                                 # we have to read and check the JSON ourselves

    if not data or "title" not in data:
        return jsonify({"detail": "title is required"}), 400

    new_todo = {
        "id": next_id,
        "title": data["title"],
        "completed": False,
    }
    todos.append(new_todo)
    next_id += 1

    return jsonify(new_todo), 201  # 201 = "Created" status code


# ---------------------------------------------------------
# Question 2: Get all tasks
# ---------------------------------------------------------
@app.route("/todos", methods=["GET"])
def get_all_todos():
    return jsonify(todos)


# ---------------------------------------------------------
# Question 3: Get a single task by ID
# ---------------------------------------------------------
@app.route("/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    for todo in todos:
        if todo["id"] == todo_id:
            return jsonify(todo)

    return jsonify({"detail": f"Task with id {todo_id} not found"}), 404


# ---------------------------------------------------------
# Question 4: Update a task
# ---------------------------------------------------------
@app.route("/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    data = request.get_json()

    for todo in todos:
        if todo["id"] == todo_id:
            if data and "title" in data:
                todo["title"] = data["title"]
            if data and "completed" in data:
                todo["completed"] = data["completed"]
            return jsonify(todo)

    return jsonify({"detail": f"Task with id {todo_id} not found"}), 404


# ---------------------------------------------------------
# Question 5: Delete a task
# ---------------------------------------------------------
@app.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    for todo in todos:
        if todo["id"] == todo_id:
            todos.remove(todo)
            return jsonify({"message": f"Task with id {todo_id} deleted successfully"})

    return jsonify({"detail": f"Task with id {todo_id} not found"}), 404


# ---------------------------------------------------------
# This runs the server when you type: python app.py
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
