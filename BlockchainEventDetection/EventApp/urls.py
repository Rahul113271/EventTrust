from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="root"),
    path("index.html", views.index, name="index"),
    path("UserLogin.html", views.UserLogin, name="UserLogin"),	      
    path("UserLoginAction", views.UserLoginAction, name="UserLoginAction"),
    path("Register.html", views.Register, name="Register"),	      
    path("RegisterAction", views.RegisterAction, name="RegisterAction"),
    path("VolunteerDashboard", views.VolunteerDashboard, name="VolunteerDashboard"),
    path("OfficerDashboard", views.OfficerDashboard, name="OfficerDashboard"),
    path("MapView", views.MapView, name="MapView"),
    path("api/events_map", views.EventsMapAPI, name="EventsMapAPI"),
    path("TrainML", views.TrainML, name="TrainML"),
    path("Predict.html", views.Predict, name="Predict"),
    path("Graph", views.Graph, name="Graph"),
    path("PredictAction", views.PredictAction, name="PredictAction"),           
    path("ViewTweets", views.ViewTweets, name="ViewTweets"), 
    path("VerifyIntegrity", views.VerifyIntegrity, name="VerifyIntegrity"),
    path("SimulateTamper", views.SimulateTamper, name="SimulateTamper"),
    path("RestoreEvent", views.RestoreEvent, name="RestoreEvent"),
    path("CastWitnessVote", views.CastWitnessVote, name="CastWitnessVote"),
    path("Logout", views.Logout, name="Logout"),
]
