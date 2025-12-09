from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
import requests
from datetime import datetime
from .models import SavedTicket

# Create your views here.

def home(request):
    return render(request, 'search.html')

def search(request):

    # Read inputs
    genre = request.GET.get('genre')
    city = request.GET.get('city')

    # Error handling with incorrect queries
    if not genre:
        if not city:
            return render(request, 'search.html', {
                "error": "City and genre cannot be empty. Please enter a city and genre."
            })
        else:
            return render(request, 'search.html', {
                "error": "Genre cannot be empty. Please enter a genre."
            })
    elif not city:
        return render(request, 'search.html', {
            "error": "City cannot be empty. Please enter a city."
        })

    # Make the API request w/helper function
    try:
        data = ticketmaster_api_request(genre, city)
    except Exception as e:
        return render(request, 'search.html', {
            "error": "Something went wrong in the API request."
        })

    # Parse raw event data into complete usable events
    raw_events = data.get("_embedded", {}).get("events", [])
    clean_events = []

    for event in raw_events:
        clean_events.append(parse_event_data(event))

    # Saved events
    saved_urls = set(SavedTicket.objects.values_list("ticket_url", flat=True))
    for event in clean_events:
        event["is_saved"] = event["ticket_url"] in saved_urls

    # Render page with results
    return render(request, 'search.html', {
        "events": clean_events,
        "genre": genre,
        "city": city,
        "event_count": len(clean_events)
    })

def ticketmaster_api_request(genre, city):

    # Setup API request
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": "pAGlnawbQc9ypv3GCrImYr7fdWgolCsc",
        "sort": "date,asc",
        "classificationName": genre,
        "city": city
    }

    # Fire API request
    response = requests.get(url, params=params)
    return response.json()

def parse_event_data(event):

    # Get all data from JSON event
    name = event["name"]
    ticket_url = event["url"]
    venue = event["_embedded"]["venues"][0]["name"]
    address = event["_embedded"]["venues"][0]["address"]["line1"]
    city = event["_embedded"]["venues"][0]["city"]["name"]
    state = event["_embedded"]["venues"][0]["state"]["name"]

    # Pick best quality image (or if None is returned, static default will be used)
    image = get_best_image(event["images"])

    # Pick date and time
    date, time = get_date_and_time(event)

    return {
        "name": name,
        "ticket_url": ticket_url,
        "image_url": image,
        "venue": venue,
        "address": address,
        "city": city,
        "state": state,
        "date": date,
        "time": time,
    }

def get_date_and_time(event):

    local_date = event.get("dates", {}).get("start", {}).get("localDate")
    local_time = event.get("dates", {}).get("start", {}).get("localTime")
    utc_dt = event.get("dates", {}).get("start", {}).get("dateTime")

    # Assume invalid unless validated
    clean_date = "Invalid Date"
    clean_time = "Invalid Time"

    # Parse the date
    if local_date:
        try:
            date_obj = datetime.strptime(local_date, "%Y-%m-%d")
            clean_date = date_obj.strftime("%a %b %-d, %Y")
        except:
            pass # Do nothing...
    elif utc_dt:
        try:
            dt = datetime.strptime(utc_dt, "%Y-%m-%dT%H:%M:%SZ")
            clean_date = dt.strftime("%a %b %-d, %Y")
        except:
            pass # Do nothing...

    # Parse the time
    if local_time:
        try:
            time_obj = datetime.strptime(local_time, "%H:%M:%S")
            clean_time = time_obj.strftime("%-I:%M %p")
        except:
            pass # Do nothing...
    elif utc_dt:
        try:
            dt = datetime.strptime(utc_dt, "%Y-%m-%dT%H:%M:%SZ")
            clean_time = dt.strftime("%-I:%M %p")
        except:
            pass # Do nothing...

    return clean_date, clean_time

def get_best_image(images):

    # Default placeholder in case there are no images from Ticketmaster API request
    if not images:
        return "/static/images/ticketmaster_default.png"

    # Choose the image with the largest width * height product
    return max(images, key=lambda img: img.get("width", 0) * img.get("height", 0))["url"]

# CRUD - Create
def save_favorite(request):

    if request.method == "POST":
        SavedTicket.objects.create(
            name=request.POST.get("name"),
            ticket_url=request.POST.get("ticket_url"),
            image_url=request.POST.get("image_url"),
            date=request.POST.get("date"),
            time=request.POST.get("time"),
            venue=request.POST.get("venue"),
            city=request.POST.get("city"),
            state=request.POST.get("state")
        )
        return JsonResponse({"saved": True})

    return JsonResponse({"error": "Something went wrong."})

    # if request.method == "POST":
    #     SavedTicket.objects.create(
    #         name=request.POST.get("name"),
    #         ticket_url=request.POST.get("ticket_url"),
    #         image_url=request.POST.get("image_url"),
    #         date=request.POST.get("date"),
    #         time=request.POST.get("time"),
    #         venue=request.POST.get("venue"),
    #         city=request.POST.get("city"),
    #         state=request.POST.get("state")
    #     )
    #
    #     genre = request.POST.get("searched_genre")
    #     city = request.POST.get("searched_city")
    #
    #     url = reverse("search") + f"?genre={genre}&city={city}"
    #     return HttpResponseRedirect(url)
    #
    # return redirect("home")

# CRUD - Read
def favorites_list(request):
    tickets = SavedTicket.objects.all()
    context = {"tickets": tickets}
    return render(request, 'favorites.html', context)

# CRUD - Update
def edit_favorite(request, id):
    if request.method == "POST":
        ticket = SavedTicket.objects.get(id=id)
        ticket.user_notes = request.POST.get("user_notes")
        ticket.save()
        return JsonResponse({"updated": True})

    return JsonResponse({"error": "Something went wrong."})

# CRUD - Delete
def remove_favorite(request):
    if request.method == "POST":
        SavedTicket.objects.filter(ticket_url=request.POST.get("ticket_url")).delete()
        return JsonResponse({"removed": True})

    return JsonResponse({"error": "Something went wrong."})

    # if request.method == "POST":
    #     ticket_url = request.POST.get("ticket_url")
    #     SavedTicket.objects.filter(ticket_url=ticket_url).delete()
    #
    #     genre = request.POST.get("searched_genre")
    #     city = request.POST.get("searched_city")
    #
    #     url = reverse("search") + f"?genre={genre}&city={city}"
    #     return HttpResponseRedirect(url)
    #
    # return redirect("home")