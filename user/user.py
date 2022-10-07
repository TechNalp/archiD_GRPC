from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from google.protobuf.json_format import MessageToJson
from werkzeug.exceptions import NotFound

import grpc
from concurrent import futures
import booking_pb2
import booking_pb2_grpc
import movie_pb2
import movie_pb2_grpc

app = Flask(__name__)

PORT = 3004
HOST = '0.0.0.0'

service = {"movie": "localhost:3001", "booking": "localhost:3003"}

with open('{}/databases/users.json'.format("."), "r") as jsf:
    users = json.load(jsf)["users"]


@app.route("/", methods=['GET'])
def home():
    return "<h1 style='color:blue'>Welcome to the User service!</h1>"


@app.route("/reservations/<userid_or_name>/<date>", methods=['GET'])
def get_bookings(userid_or_name,date):
    if userid_or_name and date:
        for user in users:
            if (user["id"] == str(userid_or_name)) or (user["name"].lower() == str(userid_or_name)).lower():
                req = requests.get(service["booking"] + "/bookings/" + user["id"])
                if req.status_code == 200:
                    bookings = req.json()
                    for booking in bookings["dates"]:
                        if booking["date"] == str(date):
                            return make_response(jsonify(booking),200)
                    return make_response(jsonify({"error":"No booking at the specified date"}), 404)

        return make_response(jsonify({"error": "user not found"}), 404)
    return make_response(jsonify({"error": "bad input"}), 400)


@app.route("/reservations/details/<userid_or_name>", methods=['GET'])
def get_reservation_details(userid_or_name):
    if userid_or_name:
        userfind = None
        for user in users:
            if (user["id"] == str(userid_or_name)) or (user["name"].lower() == str(userid_or_name).lower()):
                userfind = user
        if userfind:
            response = {"userid": userfind["id"], "bookings": []}
            rep = requests.get(service["booking"] + "/bookings/" + userfind["id"])
            if rep.status_code == 200:
                dates = rep.json()["dates"]
                for data in dates:
                    if not data["movies"]:
                        continue
                    bookingDetails = {"date": data["date"], "movies": []}
                    with grpc.insecure_channel(service["movie"]) as movieChannel:
                        for movieId in data["movies"]:
                            #req = requests.get(service["movie"] + "/movies/" + movieId)
                            stub = movie_pb2_grpc.MovieStub(movieChannel)
                            resp = stub.GetMovieByID(movie_pb2.MovieID(id=movieId))
                            if not resp["id"]:
                                bookingDetails["movies"].append(MessageToJson(resp))
                            else:
                                movieChannel.close()
                                return make_response(jsonify({"error": "impossible de trouver les informations du film ayant l'id : " + movieId}),404)
                        movieChannel.close()
                        response["bookings"].append(bookingDetails)
                return make_response(jsonify(response),200)
        return make_response(jsonify({"error": "user not found"}), 404)
    return make_response(jsonify({"error": "bad input"}), 400)


@app.route("/reservations/new/<userid_or_name>",methods=['POST'])
def new_booking_byTitle(userid_or_name):
    if userid_or_name:
        req = request.get_json()
        if req:
            with grpc.insecure_channel(service["movie"]) as movieChannel:
                stub = movie_pb2_grpc.MovieStub(movieChannel)
                for user in users:
                    if (user["id"] == str(userid_or_name)) or (user["name"].lower() == str(userid_or_name).lower()):
                        userid = user["id"]
                        #rep = requests.get(service["movie"]+"/moviesbytitle?title="+str(req["movieTitle"]))
                        resp = stub.GetMovieByTitle(movie_pb2.MovieTitle(title=str(req["movieTitle"])))
                        if resp["id"]:
                            movieId = str(resp["id"])
                            rep = requests.post(service["booking"]+"/bookings/"+userid,json={"date":req["date"],"movieid":movieId})
                            if rep.status_code == 200:
                                movieChannel.close()
                                return make_response(jsonify(rep.json()),200)
                            elif rep.status_code == 409:
                                movieChannel.close()
                                return make_response(jsonify({"error":"Cette réservation existe déjà"}),409)
                            movieChannel.close()
                            return make_response(jsonify({"error":"Requête incorrecte"}),400)
                        movieChannel.close()
                        return make_response(jsonify({"error":"Impossible de trouver l'id du film"}),404)
                movieChannel.close()
                return make_response(jsonify({"error":"Impossible de trouver l'utilisateur"}),404)
    return make_response(jsonify({"error": "Requête incorrecte"}), 400)
if __name__ == "__main__":
    print("Server running in port %s" % (PORT))
    app.run(host=HOST, port=PORT)
