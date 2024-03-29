import math

import grpc
from concurrent import futures
import movie_pb2
import movie_pb2_grpc
import json

class MovieServicer(movie_pb2_grpc.MovieServicer): # On crée une classe qui hérite de MovieServicer afin de créer les surcharges de fonction pour les appels gRPC

    def __init__(self):
        with open('{}/data/movies.json'.format("."), "r") as jsf:
            self.db = json.load(jsf)["movies"]

    def GetMovieByID(self, request, context):
        print("Récupération d'un film via son id")
        for movie in self.db: # On cherche le film ayant le bon id et on retourne les informations trouvé
            if movie['id'] == request.id:
                print("Movie found!")
                return movie_pb2.MovieData(title=movie['title'], rating=float(movie['rating']), director=movie['director'],id=movie['id'])
        return movie_pb2.MovieData(title="", rating=0.0, director="", id="")

    def GetListMovies(self, request, context):
        for movie in self.db: # On retourne progressivement (via le yield) toutes les infos sur tous les films
            yield movie_pb2.MovieData(title=movie['title'],rating=float(movie['rating']),director=movie['director'],id=movie['id'])

    def CreateMovie(self, request,contect):
        print("Tentative d'ajout d'un film dans la bdd:")
        for movie in self.db: # On vérifie que le film que l'on veut créer n'existe pas déjà
            if movie["id"] == str(request.id):
                print("- Film déjà présent dans la base")
                return movie_pb2.MovieData(title="", rating=0.0, director="",id="")
        self.db.append({"title":request.title,"rating":request.rating,"director":request.director,"id":request.id}) # On ajoute le film à la bdd
        print("- Film ajoutée: ")
        print(self.db)
        return movie_pb2.MovieData(title=request.title,rating=request.rating,director=request.director,id=request.id)

    def DelMovie(self, request, context):
        print("Tentative de suppression d'un film avec l'id : ",request.id)
        for movie in self.db: # On cherche le film à supprimer de la bdd
            if movie["id"] == request.id:
                self.db.remove(movie)
                print("- Success")
                return movie_pb2.MovieID(id=movie["id"])
        print("- Fail")
        return movie_pb2.MovieID(id="") # Si aucun film n'avait le bon id

    def UpdateMovieRating(self, request, context):
        print("Tentative de mise à jour du rating du film avec l'id : "+request.id)
        for movie in self.db: # On cherche le film avec le bon id pour mettre à jour sa note
            if movie["id"] == request.id:
                movie["rating"] = round(request.rating,1)
                print("- Success")
                return movie_pb2.MovieData(title=movie["title"],id=movie["id"],rating= float(movie["rating"]),director=movie["director"])
        print("- Fail")
        return movie_pb2.MovieData(title="", id="", rating=0.0,director="") # Si on ne trouve pas le film

    def GetMovieByTitle(self, request, context):
        print("Récupération d'un film via son titre")
        for movie in self.db: # On cherche le film ayant le bon nom et on retourne ses informations
            if movie["title"].lower() == request.title.lower():
                print(" - Success")
                return movie_pb2.MovieData(title=movie["title"],id=movie["id"],rating= float(movie["rating"]),director=movie["director"])
        print(" - Not found")
        return movie_pb2.MovieData(title="", id="", rating=0.0,director="") # Si aucun film n'a de titre correspondant
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    movie_pb2_grpc.add_MovieServicer_to_server(MovieServicer(), server)
    server.add_insecure_port('[::]:3001')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()