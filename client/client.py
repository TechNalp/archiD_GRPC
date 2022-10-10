import sys
import time

import grpc

import booking.booking_pb2
import movie_pb2
import movie_pb2_grpc

import showtime_pb2
import showtime_pb2_grpc

import booking_pb2
import booking_pb2_grpc

TIMEOUT_DELAY = 2 # Définie le temps d'attente maximal en seconde pour la récéption d'une réponse du serveur avant de considérer qu'il y a un problème avec le service distant

def get_movie_by_id(stub,id):
    movie = stub.GetMovieByID(id,timeout=TIMEOUT_DELAY) #On définit un timeout à la requête
    print(movie)

def get_list_movies(stub):
    allmovies = stub.GetListMovies(movie_pb2.Empty(),timeout=TIMEOUT_DELAY)  #Appel gRPC avec un timeout
    for movie in allmovies:
        print("Movie called %s" % (movie.title))
def create_movie(stub,movie):
    if not movie["id"] : #On verifie que id ne vaut pas null et n'est pas une chaîne vide
        print("Id invalide")
        return
    response = stub.CreateMovie(movie_pb2.MovieData(title=movie["title"],id=movie["id"],rating=movie["rating"],director=movie["director"]),timeout=TIMEOUT_DELAY) #Appel gRPC avec un timeout
    if response.id == "": #Permet de vérifier si il y a eu une erreur de n'importe qu'elle type du côté serveur
        print("Erreur lors de l'ajout")
    else:
        print("Film ajouté : ")
        print(response)

def update_movie_rating(stub,id,new_rating):
    if not id or new_rating <0: #On vérifie que l'id n'est pas null ou une chaîne vide et que la nouvelle note est supérieur ou égale à 0
        print("Id ou nouvelle note invalide")
        return
    response = stub.UpdateMovieRating(movie_pb2.MovieUpdateRating(id=id,rating=float(new_rating)),timeout=TIMEOUT_DELAY) #Appel gRPC avec un timeout
    if response.id == "": #Permet de vérifier si il y a eu une erreur de n'importe qu'elle type du côté serveur
        print("Erreur lors de l'update")
    else:
        print("Note mise à jour !")

def del_movie(stub,id):
    response = stub.DelMovie(movie_pb2.MovieID(id=id),timeout=TIMEOUT_DELAY) #Appel gRPC avec un timeout
    if response.id == "": #Permet de vérifier si il y a eu une erreur de n'importe qu'elle type du côté serveur
        print("Erreur lors de la suppression")
    else:
        print("Film supprimé !")

def get_movie_bytitle(stub,title):
    if not title: #On verifie que title ne vaut pas null et n'est pas une chaîne vide
        print("Le nom du film n'est pas valide")
        return
    response = stub.GetMovieByTitle(movie_pb2.MovieTitle(title = title),timeout=TIMEOUT_DELAY) #Appel gRPC avec un timeout
    if response.id == "": #Permet de vérifier si il y a eu une erreur de n'importe qu'elle type du côté serveur
        print("Erreur lors de la récupération du film")
    else:
        print("Film trouvé :")
        print(response)


def get_schedule(stub):
    print("Récupération de toute la BDD de showtime:")
    response = stub.GetSchedule(showtime_pb2.ScheduleEmpty(),timeout=TIMEOUT_DELAY) #Appel gRPC avec un timeout
    print("Liste des schedules:")
    for schedule in response: # On affiche chaque réponse reçu via le stream du serveur
        print(" -",end=" ")
        print(schedule)

def get_movies_bydate(stub,date):
    if not date:  # On regarde si la date n'est pas null et n'est pas une chaîne vide
        print("La date spécifié n'est pas valide")
        return
    print("Récupération des films du showTime à la date: ",date)
    response = stub.GetMoviesByDate(showtime_pb2.Date(date=date),timeout=TIMEOUT_DELAY)  # Appel gRPC avec un timeout
    if response.date: # On vérifie que la réponse du serveur est valide
        print(response)
    else:
        print("Erreur lors de la récupération")


def get_json(stub):
    print("Récupération de toutes les réservations de la BDD")
    response = stub.get_json(booking_pb2.EmptyBooking(),timeout=TIMEOUT_DELAY) # Appel gRPC avec un timeout
    for booking in response:
        print("-----------\n",booking)

def get_booking_for_user(stub, userid):
    if not userid: # On regarde si l'userId n'est pas null et n'est pas une chaîne vide
        print("UserId n'est pas valide")
        return
    print("Récupération des réservation de l'utilisateur: ",userid)
    response = stub.get_booking_for_user(booking_pb2.UserId(userid=userid),timeout=TIMEOUT_DELAY) # Appel gRPC avec un timeout
    if response.dates: # On vérifie que la réponse reçue est valide
        print(response)
    else:
        print("Erreur lors de la récupération des informations")

def add_booking_byuser(stub,userid,date,movieid):
    if not userid or not date or not movieid: # on vérifie que les paramètres sont valides
        print("Un ou plusieurs paramètres ne sont pas valides")
        return
    print("Ajout du film ayant l'id: ",movieid," à la réservation de la date: ",date," pour l'utilisateur: ",userid)
    response = stub.add_booking_byuser(booking_pb2.AddBooking(userid=userid,date=date,movieid=movieid),timeout=TIMEOUT_DELAY) # Appel gRPC avec un timeout
    if response.dates: # On vérifie que la réponse reçue est valide
        print("Film ajouté avec succès")
    else:
        print("Erreur lors de l'ajout du film")

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    print("============TEST SERVICE MOVIE=================")
    with grpc.insecure_channel('localhost:3001') as channel: # On ouvre un canal avec le serveur hébergeant le service gRPC movie
        stub = movie_pb2_grpc.MovieStub(channel) # On crée le stub client
        try:
            print("-------------- GetMovieByID --------------")
            movieid = movie_pb2.MovieID(id="a8034f44-aee4-44cf-b32c-74cf452aaaae")
            get_movie_by_id(stub, movieid)

            print("-------------- GetListMovies --------------")
            get_list_movies(stub)

            print("-------------- CreateMovie --------------")
            create_movie(stub,{"title":"Interstallar","rating":8.9,"id":"124KFHD","director":"Mathis Planchet"})

            print("-------------- DeleteMovie --------------")
            del_movie(stub,"720d006c-3a57-4b6a-b18f-9b713b073f3c")

            print("-------------- UpdateRating --------------")
            update_movie_rating(stub,"a8034f44-aee4-44cf-b32c-74cf452aaaae",3.3)

            print("-------------- GetMovieByTitle --------------")
            get_movie_bytitle(stub,"The Martian")
        except Exception as e: # On capture toute les exceptions
            if isinstance(e,grpc._channel._MultiThreadedRendezvous) or isinstance(e,grpc._channel._InactiveRpcError): # On vérifie que l'excepiton soulevée est bien causé par gRPC
                if(e.code() == grpc.StatusCode.DEADLINE_EXCEEDED): # On vérifie qu'il s'agit bien d'une exception causé par un timeout
                    print("SERVICE MOVIE INACTIF",file=sys.stderr) # On affiche le message sur la sortie standard d'erreur
                    sys.stderr.flush()
                    time.sleep(0.5) # Pour avoir le temps de voir le message avant de passer à la suite
                else: # Si il s'agit d'une exception qui n'est pas causé par un timeout, on propage l'exception pour qu'elle continue sa remontée
                    raise e
            else: # Si il ne s'agit pas d'une exception causé par gRPC, on propage l'exception pour qu'elle continue sa remontée
                raise e
    channel.close()# On ferme le canal par précaution (normalement le with le fait)
    print("============TEST SERVICE TIME=================")
    with grpc.insecure_channel('localhost:3002') as channel: # On ouvre un canal avec le serveur hébergeant le service gRPC time
        stub = showtime_pb2_grpc.ShowtimeStub(channel) # On crée le stub client
        try:
            print("-------------- GetSchedule --------------")
            get_schedule(stub)
            print("-------------- GetMoviesByDate --------------")
            get_movies_bydate(stub,"20151130")
        except Exception as e: # On capture toute les exceptions
            if isinstance(e, grpc._channel._MultiThreadedRendezvous) or isinstance(e,grpc._channel._InactiveRpcError):  # On vérifie que l'excepiton soulevée est bien causé par gRPC
                if (e.code() == grpc.StatusCode.DEADLINE_EXCEEDED):  # On vérifie qu'il s'agit bien d'une exception causé par un timeout
                    print("SERVICE MOVIE INACTIF", file=sys.stderr) # On affiche le message sur la sortie standard d'erreur
                    sys.stderr.flush()
                    time.sleep(0.5)  # Pour avoir le temps de voir le message avant de passer à la suite
                else:  # Si il s'agit d'une exception qui n'est pas causé par un timeout, on propage l'exception pour qu'elle continue sa remontée
                    raise e
            else:  # Si il ne s'agit pas d'une exception causé par gRPC, on propage l'exception pour qu'elle continue sa remontée
                raise e
    channel.close() # On ferme le canal par précaution (normalement le with le fait)

    print("============TEST SERVICE BOOKING=================")
    with grpc.insecure_channel('localhost:3003') as channel:  # On ouvre un canal avec le serveur hébergeant le service gRPC time
        stub = booking_pb2_grpc.BookingStub(channel)  # On crée le stub client
        try:
            print("-------------- GetJSON --------------")
            get_json(stub)
            print("-------------- GetBookingForUser --------------")
            get_booking_for_user(stub,"dwight_schrute")
            print("-------------- AddBookingByUser --------------")
            add_booking_byuser(stub,"peter_curley","20151203","39ab85e5-5e8e-4dc5-afea-65dc368bd7ab")
        except Exception as e:  # On capture toutes les exceptions
            if isinstance(e, grpc._channel._MultiThreadedRendezvous) or isinstance(e,grpc._channel._InactiveRpcError): # On vérifie que l'excepiton soulevée est bien causé par gRPC
                if (e.code() == grpc.StatusCode.DEADLINE_EXCEEDED):  # On vérifie qu'il s'agit bien d'une exception causé par un timeout
                    print("SERVICE BOOKING INACTIF",file=sys.stderr)  # On affiche le message sur la sortie standard d'erreur
                    sys.stderr.flush()
                    time.sleep(0.5)  # Pour avoir le temps de voir le message avant de passer à la suite
                else:  # Si il s'agit d'une exception qui n'est pas causé par un timeout, on propage l'exception pour qu'elle continue sa remontée
                    raise e
            else:  # Si il ne s'agit pas d'une exception causée par gRPC, on propage l'exception pour qu'elle continue sa remontée
                raise e
    channel.close()  # On ferme le canal par précaution (normalement le with le fait)

if __name__ == '__main__':
    run()
