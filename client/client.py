import sys
import time

import grpc




import movie_pb2
import movie_pb2_grpc

import showtime_pb2
import showtime_pb2_grpc


TIMEOUT_DELAY = 2

def get_movie_by_id(stub,id):
    movie = stub.GetMovieByID(id,timeout=TIMEOUT_DELAY)
    print(movie)

def get_list_movies(stub):
    allmovies = stub.GetListMovies(movie_pb2.Empty(),timeout=TIMEOUT_DELAY)
    for movie in allmovies:
        print("Movie called %s" % (movie.title))
def create_movie(stub,movie):
    if not movie["id"] :
        print("Id invalide")
        return
    response = stub.CreateMovie(movie_pb2.MovieData(title=movie["title"],id=movie["id"],rating=movie["rating"],director=movie["director"]),timeout=TIMEOUT_DELAY)
    if response.id == "":
        print("Erreur lors de l'ajout")
    else:
        print("Film ajouté : ")
        print(response)

def update_movie_rating(stub,id,new_rating):
    if not id or new_rating <0:
        print("Id ou nouvelle note invalide")
        return
    response = stub.UpdateMovieRating(movie_pb2.MovieUpdateRating(id=id,rating=float(new_rating)),timeout=TIMEOUT_DELAY)
    if response.id == "":
        print("Erreur lors de l'update")
    else:
        print("Note mise à jour !")

def del_movie(stub,id):
    response = stub.DelMovie(movie_pb2.MovieID(id=id),timeout=TIMEOUT_DELAY)
    if response.id == "":
        print("Erreur lors de la suppression")
    else:
        print("Film supprimé !")

def get_movie_bytitle(stub,title):
    if not title:
        print("Le nom du film n'est pas valide")
        return
    response = stub.GetMovieByTitle(movie_pb2.MovieTitle(title = title),timeout=TIMEOUT_DELAY)
    if response.id == "":
        print("Erreur lors de la récupération du film")
    else:
        print("Film trouvé :")
        print(response)


def get_schedule(stub):
    print("Récupération de toute la BDD de showtime:")
    response = stub.GetSchedule(showtime_pb2.ScheduleEmpty(),timeout=TIMEOUT_DELAY)
    print("Liste des schedules:")
    for schedule in response:
        print(" -",end=" ")
        print(schedule)

def get_movies_bydate(stub,date):
    if not date:
        print("La date spécifié n'est pas valide")
        return
    print("Récupération des films à la date : ",date)
    response = stub.GetMoviesByDate(showtime_pb2.Date(date=date))
    print(response)
def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    print("============TEST SERVICE MOVIE=================")
    with grpc.insecure_channel('localhost:3001') as channel:
        stub = movie_pb2_grpc.MovieStub(channel)
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
        except Exception as e:
            if isinstance(e,grpc._channel._MultiThreadedRendezvous) or isinstance(e,grpc._channel._InactiveRpcError):
                if(e.code() == grpc.StatusCode.DEADLINE_EXCEEDED):
                    print("SERVICE MOVIE INACTIF",file=sys.stderr)
                    sys.stderr.flush()
                    time.sleep(0.5)
                else:
                    raise e
    channel.close()
    print("============TEST SERVICE TIME=================")
    with grpc.insecure_channel('localhost:3002') as channel:
        stub = showtime_pb2_grpc.ShowtimeStub(channel)
        try:
            print("-------------- GetSchedule --------------")
            get_schedule(stub)
            print("-------------- GetMoviesByDate --------------")
            get_movies_bydate(stub,"20151130")
        except Exception as e:
            if isinstance(e, grpc._channel._MultiThreadedRendezvous) or isinstance(e, grpc._channel._InactiveRpcError):
                if (e.code() == grpc.StatusCode.DEADLINE_EXCEEDED):
                    print("SERVICE TIME INACTIF",file=sys.stderr)
                    sys.stderr.flush()
                    time.sleep(0.5)
                else:
                    raise e
    channel.close()

if __name__ == '__main__':
    run()
