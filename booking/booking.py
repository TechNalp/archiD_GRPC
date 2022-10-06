from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from werkzeug.exceptions import NotFound

app = Flask(__name__)

PORT = 3201
HOST = '0.0.0.0'

service = {"showTime": "http://host.docker.internal:3202"}

with open('{}/databases/bookings.json'.format("."), "r") as jsf:
   bookings = json.load(jsf)["bookings"]

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Booking service!</h1>"


@app.route("/bookings",methods=['GET'])
def get_json():
   return make_response(jsonify(bookings),200)

@app.route("/bookings/<userid>",methods=['GET'])
def get_booking_for_user(userid):
   if userid:
      for booking in bookings:
         if booking["userid"] == str(userid):
           return make_response(jsonify(booking),200)
   return make_response(jsonify({"error":"bad input parameter"}),400)




@app.route("/bookings/<userid>",methods=['POST'])
def add_booking_byuser(userid):
   if userid:
      req = request.get_json()
      showTime = requests.get(service["showTime"] + "/" + req["date"])
      if showTime.status_code != 200:
         return make_response(jsonify({"error": "bad input"}), 400)
      for movieId in showTime.json():
         if movieId == req["movieid"]:
            for booking in bookings:
               if booking["userid"] == str(userid):
                  for reservation in booking["dates"]:
                     if reservation["date"] == str(req["date"]):
                        for id in reservation["movies"]:
                           if id == str(req["movieid"]):
                              return make_response(jsonify({"error": "an existing item already exists"}), 409)
                        reservation["movies"].append(str(req["movieid"]))
                        return make_response(jsonify(booking), 200)
                  booking["dates"].append({"date": str(req["date"]), "movies": [str(req["movieid"])]})
                  return make_response(jsonify(booking), 200)
            newBooking = {"userid": userid, "dates": [{"date": req["date"], "movies": [req["movieid"]]}]}
            bookings.append(newBooking)
            return make_response(jsonify(newBooking), 200)
      return make_response(jsonify({"error":"bad input"}),400)



if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
