from flask import Flask, jsonify
app = Flask(__name__)


@app.route("/")
def index():
    return "Welcome to Flask appliaction created by Serverless Framework."


@app.route("/users")
def users():
    users = [{'name': 'test1'}, {'name': 'test2'}]
    return jsonify(data=users)


@app.route("/users/<id>")
def user(id):
    return jsonify(data={'name': 'test1'})
