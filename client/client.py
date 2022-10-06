import grpc

import movie_pb2
import movie_pb2_grpc


def get_movie_by_id(stub,id):
    movie = stub.GetMovieByID(id)
    print(movie)

def get_list_movies(stub):
    allmovies = stub.GetListMovies(movie_pb2.Empty())
    for movie in allmovies:
        print("Movie called %s" % (movie.title))
def create_movie(stub,movie):
    if not movie["id"] :
        print("Id invalide")
        return
    response = stub.CreateMovie(movie_pb2.MovieData(title=movie["title"],id=movie["id"],rating=movie["rating"],director=movie["director"]))
    if response.id == "":
        print("Erreur lors de l'ajout")
    else:
        print("Film ajouté : ")
        print(response)

def update_movie_rating(stub,id,new_rating):
    if not id or new_rating <0:
        print("Id ou nouvelle note invalide")
        return
    response = stub.UpdateMovieRating(movie_pb2.MovieUpdateRating(id=id,rating=float(new_rating)))
    if response.id == "":
        print("Erreur lors de l'update")
    else:
        print("Note mise à jour !")

def del_movie(stub,id):
    response = stub.DelMovie(movie_pb2.MovieID(id=id))
    if response.id == "":
        print("Erreur lors de la suppression")
    else:
        print("Film supprimé !")

def get_movie_bytitle(stub,title):
    if not title:
        print("Le nom du film n'est pas valide")
        return
    response = stub.GetMovieByTitle(movie_pb2.MovieTitle(title = title))
    if response.id == "":
        print("Erreur lors de la récupération du film")
    else:
        print("Film trouvé :")
        print(response)


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:3001') as channel:
        stub = movie_pb2_grpc.MovieStub(channel)

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
    channel.close()

if __name__ == '__main__':
    run()
