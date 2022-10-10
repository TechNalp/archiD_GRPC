import asyncio
import time

from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from google.protobuf.json_format import MessageToJson
from werkzeug.exceptions import NotFound

import grpc
from concurrent import futures

import booking.booking_pb2_grpc
import booking_pb2
import booking_pb2_grpc
import movie_pb2
import movie_pb2_grpc

app = Flask(__name__)
PORT = 3004
HOST = '0.0.0.0'

service = {"movie": "localhost:3001", "booking": "localhost:3003"} # Dictionnaire permettant de facilement modifier les adresses des services

with open('{}/data/users.json'.format("."), "r") as jsf:
    users = json.load(jsf)["users"]


@app.route("/", methods=['GET'])
def home():
    return "<h1 style='color:blue'>Welcome to the User service!</h1>"



@app.route("/reservations/<userid_or_name>/<date>", methods=['GET']) # Récupération des reservations d'un user (via son id/nom) à une certaine date
def get_booking(userid_or_name,date):
    if userid_or_name and date: # On vérifie que les paramêtres ne sont pas null et ne sont pas des chaînes vides
        for user in users: # Pour chaque utilisateur dans la bdd, on cherche celui qui à soit le bon id soit le bon nom
            if (user["id"] == str(userid_or_name)) or (user["name"].lower() == str(userid_or_name).lower()):
                with grpc.insecure_channel(service["booking"]) as bookingChannel: # On ouvre un canal avec le serveur gRPC hebergeant le service booking
                    stubBooking = booking_pb2_grpc.BookingStub(bookingChannel) # On crée le stub client
                    req = stubBooking.get_booking_for_user(booking_pb2.UserId(userid=user["id"])) # On récupére la liste des bookings de l'utilisateur via un appel gRPC
                    if req.userid: # On vérifie si le serveur à renvoyé une réponse valide (req.userid != null et != "")
                        for booking in req.dates: # On verifie si la date passé en paramètre de l'url fait bien partie des dates de réservations de l'utilisateur
                            if booking.date == str(date): # Si la date fait partie des réservtions, on retourne la date et la liste des id des films associés
                                return make_response(jsonify({"date":booking.date,"movies":[movieId for movieId in booking.movies]}),200)
                        return make_response(jsonify({"error":"No booking at the specified date"}), 404) # Si la date passé par l'url ne fait pas partie des réservation de l'utilisateur, on retourne une erreur
                bookingChannel.close() #On ferme le canal
        return make_response(jsonify({"error": "user not found"}), 404) # Si aucun n'utilisateur n'a un id ou un nom correspondant à celui passé en paramètre
    return make_response(jsonify({"error": "bad input"}), 400) # Si les paramètre passé par l'url ne sont pas valide


@app.route("/reservations/details/<userid_or_name>", methods=['GET']) # Récupération de toute les reservavations (avec les informations sur les films) d'un utilisateur via son id/nom
def get_reservation_details(userid_or_name):
    if userid_or_name: # On vérifie que le paramètre n'est pas null et n'est pas une chaîne vide
        userfind = None # Servira à stocker les informations de l'utilisateur trouvé
        for user in users: # On regarde si un utilisateur a un id ou un nom correspondant à la valeur passé en paramètre
            if (user["id"] == str(userid_or_name)) or (user["name"].lower() == str(userid_or_name).lower()):
                userfind = user # On stocke les informations de l'utilisateur trouvé
        if userfind: # Si l'on a trouvé un utilisateur existant
            response = {"userid": userfind["id"], "bookings": []} # On prépare la "base" de la réponse que l'on retournera
            with grpc.insecure_channel(service["booking"]) as bookingChannel: # On ouvre un canal avec le serveur gRPC hebergeant le service booking
                stubBooking = booking_pb2_grpc.BookingStub(bookingChannel) # On crée le stub client
                rep = stubBooking.get_booking_for_user(booking_pb2.UserId(userid=user["id"])) # On récupére la liste des bookings de l'utilisateur via un appel gRPC
                if rep.userid: # On vérifie que le serveur retourne une réponse valide
                    dates = rep.dates
                    for data in dates: # Pour chaque date associée à l'utilisateur
                        if not data.movies: # Si la date n'a aucun film associé on passe à la date suivante
                            continue
                        bookingDetails = {"date": data.date, "movies": []} # Si des films sont associés à la date, on prépare la "base" qui servira pour stocker les détails des films
                        with grpc.insecure_channel(service["movie"]) as movieChannel: # On ouvre un canal avec le serveur gRPC hebergeant le service movie
                            stubMovie = movie_pb2_grpc.MovieStub(movieChannel) # on crée le stub client pour le service movie
                            for movieId in data.movies: # Pour chaque film de la date en cours de traitement
                                resp = stubMovie.GetMovieByID(movie_pb2.MovieID(id=movieId)) # On récupère les informations sur le film grâce à son id et un appele gRPC
                                if not resp.id == "": # On vérifie que la réponse du serveur est valide
                                    bookingDetails["movies"].append(MessageToJson(resp)) # Si la réponse est valide, on ajoute les détails du film à la liste des détails de film pour la date en cours et qui sera utilisé dans la réponse
                                else: # Si le serveur retourne une réponse invalide, c'est que l'un des ids transmis n'est pas valide; on stoppe la recherche et on retourne une erreur
                                    bookingChannel.close()
                                    movieChannel.close()
                                    return make_response(jsonify({"error": "impossible de trouver les informations du film ayant l'id : " + movieId}),404)
                            movieChannel.close()
                            response["bookings"].append(bookingDetails) # Si l'on a réussi à récupérer les détails de tous les films à la date en cours de test, on ajoute tous les détails à la réponse globale et on passe à la recherche pour la date suivante
                    return make_response(jsonify(response),200) # Quand toutes les dates ont été parcourues, on retourne la réponse compète
        return make_response(jsonify({"error": "user not found"}), 404) # Si l'on n'a pas trouvé d'utilisateur avec le bon id ou le bon nom, on retourne une errueur
    return make_response(jsonify({"error": "bad input"}), 400) # Si le paramètre passé dans l'url n'est pas bon


@app.route("/reservations/new/<userid_or_name>",methods=['POST']) # Création d'une nouvelle reservation pour un user avec le film et la date passés dans le body
def new_booking_byTitle(userid_or_name):
    if userid_or_name: # On vérifie que le paramètre n'est pas null et n'est pas une chaîne vide
        req = request.get_json() # On récupère le body de la requête
        if req: # Si le body n'est pas null/vide
            with grpc.insecure_channel(service["movie"]) as movieChannel: # On ouvre un canal avec le serveur gRPC hebergeant le service movie
                stub = movie_pb2_grpc.MovieStub(movieChannel) # On crée le stub client pour le service movie
                for user in users: # On cherche si un utilisateur a son id ou son nom qui correspond avec le paramètre
                    if (user["id"] == str(userid_or_name)) or (user["name"].lower() == str(userid_or_name).lower()):
                        userid = user["id"] # On sauvegarde l'id de l'utilisateur trouvé
                        resp = stub.GetMovieByTitle(movie_pb2.MovieTitle(title=str(req["movieTitle"]))) # On récupère les informations du film via son titre récupéré dans le body de la requête
                        if resp["id"]: # On vérifie que la réponse du serveur est valide
                            movieId = str(resp["id"]) # On stocke l'id du film récupéré
                            with grpc.insecure_channel(service["booking"]) as bookingChannel: # On ouvre un canal avec le serveur gRPC hebergeant le service booking
                                stubBooking = booking_pb2_grpc.BookingStub(bookingChannel) # On crée le stub client pour le service booking
                                rep = stubBooking.add_booking_byuser(booking_pb2.AddBooking(userid=userid,date=req["date"],movieid=movieId)) # On crée la réservation avec un appel gRPC
                                if rep.userid: # On vérifie que l'ajout à bien fonctionné
                                    bookingChannel.close()
                                    movieChannel.close()
                                    return make_response(jsonify(rep.json()),200)
                                else:
                                    return make_response(jsonify({"error":"Impossible de créer la réservation"}),409)
                        return make_response(jsonify({"error":"Impossible de trouver l'id du film"}),404)
                movieChannel.close()
                return make_response(jsonify({"error":"Impossible de trouver l'utilisateur"}),404)
    return make_response(jsonify({"error": "Requête incorrecte"}), 400)


if __name__ == "__main__":
    print("Server running in port %s" % (PORT))
    app.run(host=HOST, port=PORT)
