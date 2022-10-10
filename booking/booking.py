import grpc
from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from werkzeug.exceptions import NotFound
from google.protobuf.json_format import MessageToJson
from concurrent import futures

import showtime_pb2
import showtime_pb2_grpc

import booking_pb2
import booking_pb2_grpc

app = Flask(__name__)

PORT = 3003
HOST = '0.0.0.0'

service = {"showTime": "localhost:3002"}



class BookingServicer(booking_pb2_grpc.BookingServicer): # On crée une classe qui hérite de BookingServicer afin de créer les surcharges de fonction pour les appels gRPC
    def __init__(self):
        with open('{}/data/bookings.json'.format("."), "r") as jsf:
            self.bookings = json.load(jsf)["bookings"]

    def get_json(self, request, context):
        print("Récupération de toute la bdd")
        for booking in self.bookings: # Pour chaque utilisateur, on crée une liste qui contiendra toutes ses réservation et on retourne progressivement chaque liste (via le yield)
            dateItem = []
            for date in booking["dates"]:
                dateItem.append(booking_pb2.DateItem(date=date["date"], movies=date["movies"]))
            yield booking_pb2.BookingsUser(dates=dateItem, userid=booking["userid"])

    def get_booking_for_user(self, request, context):
        if request.userid: # On vérifie que le paramètre est valide (pas null et pas une chaîne vide)
            print("Récupération des réservation de l'utilisateur: ",request.userid)
            for booking in self.bookings: # On recherche les reservations de l'utilisateur choisi
                if booking["userid"] == str(request.userid):
                    dateItem = [] # Liste qui contiendra toutes les réservations de l'utilisateur
                    for date in booking["dates"]: # Pour chaque réservation de l'utilisateur, on l'ajoute à la liste sous forme d'un objet gRPC DateItem
                        dateItem.append(booking_pb2.DateItem(date=date["date"], movies=date["movies"]))
                    return booking_pb2.BookingsUser(dates=dateItem, userid=booking["userid"])
        return booking_pb2.BookingsUser(dates=[], userid="")

    def add_booking_byuser(self, request, context):
        if request.userid and request.date and request.movieid: # On vérifie que l'on a les informations nécessaires
            print("Ajout du film ayant l'id: ",request.movieid," à la réservation de la date: ",request.date," pour l'utilisateur: ",request.userid)
            req = json.loads(MessageToJson(request)) # On transforme en json l'objet gRPC reçue
            with grpc.insecure_channel(service["showTime"]) as channel: # On ouvre un canal avec le serveur hébergeant le service gRPC Time
                stub = showtime_pb2_grpc.ShowtimeStub(channel) # On crée le stub client pour le service time
                showTime = stub.GetMoviesByDate(showtime_pb2.Date(date=req["date"])) # On récupère la liste des films dans le planning à la date voulue via un appel gRPC
                if not showTime.date: # Si la réponse du serveur est invalide
                    return booking_pb2.BookingsUser(dates=[], userid="")
            channel.close()
            for movieId in showTime.movies: # Pour chaque film récupéré
                if movieId == req["movieid"]: # On vérifie que l'id du film que l'on veut ajouter au booking fait bien partie de la liste reçu par le service time
                    for booking in self.bookings: # On cherche les réservations de l'utilisateur
                        if booking["userid"] == str(req["userid"]): # Si l'on trouve que l'utiilisateur à déjà au moins une réservation
                            for reservation in booking["dates"]: # On cherche si l'utilisateur à déjà des films réservé à la date voulu
                                if reservation["date"] == str(req["date"]): # Si il y a déjà des films réservés à cette date
                                    for id in reservation["movies"]: # On vérifie que le film n'existe pas déjà dans la réservation de l'utilisateur
                                        if id == str(req["movieid"]):
                                            return booking_pb2.BookingsUser(dates=[], userid="") # Si le film est déjà présent dans la réservatiion
                                    reservation["movies"].append(str(req["movieid"])) # Si le film n'est pas déjà présent dans la réservation, on l'ajoute
                                    return booking_pb2.BookingsUser(userid=booking["userid"], dates=[booking_pb2.DateItem(date=req["date"], movies=[req["movieid"]])])
                            booking["dates"].append({"date": str(req["date"]), "movies": [str(req["movieid"])]}) # Si il s'agit de la première réservation à cette date
                            return booking_pb2.BookingsUser(userid=booking["userid"],dates=[booking_pb2.DateItem(**x) for x in booking["dates"]])
                    newBooking = {"userid": req["userid"], "dates": [{"date": req["date"], "movies": [req["movieid"]]}]} # Si il s'agit de la première réservation de l'utilisateur
                    self.bookings.append(newBooking)
                    return booking_pb2.BookingsUser(userid=newBooking["userid"],dates=[booking_pb2.DateItem(date=req["date"],movies=[req["movieid"]])])
            return booking_pb2.BookingsUser(dates=[], userid="")
        return booking_pb2.BookingsUser(dates=[], userid="")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bookingService = BookingServicer()
    booking_pb2_grpc.add_BookingServicer_to_server(bookingService, server)
    server.add_insecure_port('[::]:3003')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

