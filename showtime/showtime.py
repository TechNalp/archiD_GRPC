import grpc
from concurrent import futures
import showtime_pb2
import showtime_pb2_grpc
import json



class ShowtimeServicer(showtime_pb2_grpc.ShowtimeServicer): # On crée une classe qui hérite de ShowtimeServicer afin de créer les surcharges de fonction pour les appels gRPC

    def __init__(self):
        with open('{}/data/times.json'.format("."), "r") as jsf:
            self.db = json.load(jsf)["schedule"]

    def GetSchedule(self,request,context):
        print("Récupération de toute la BDD")
        for schedule in self.db: # On retourne progressivement (via le yield) toutes les infos sur tous les plannings
            yield showtime_pb2.Schedule(date=schedule["date"],movies=schedule["movies"])

    def GetMoviesByDate(self,request, context):
        if request.date: # On vérifie que la date reçue est bien valide
            print("Récupérations des films à la date : ", request.date)
            for schedule in self.db: # On cherche le planning à la bonne date
                if schedule["date"] == request.date:
                    print(" - Success")
                    return showtime_pb2.Schedule(date=schedule["date"],movies=schedule["movies"]) # On retourne le planning trouvé
        print("Récupérations des films à la date : ERREUR DATE")
        print(" - Failed")
        return showtime_pb2.Schedule(date="",movies=[]) # Si aucun planning n'a été trouvé à la date indiquée

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    showtime_pb2_grpc.add_ShowtimeServicer_to_server(ShowtimeServicer(), server)
    server.add_insecure_port('[::]:3002')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
