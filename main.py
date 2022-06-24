import json
import pathlib
from typing import List, Union

from fastapi import FastAPI, Response, Depends
from sqlmodel import Session, select

from models import Track
from database import TrackModel, engine

# instantiate the FastAPI app
app = FastAPI()

# create container for our data - to be loaded at app startup.
data = []

@app.on_event("startup")
async def startup_event():
    DATAFILE = pathlib.Path() / 'data' / 'tracks.json'
    with open(DATAFILE, 'r') as f:
        tracks = json.load(f)
        for track in tracks:
            data.append(Track(**track).dict())


@app.get('/tracks/', response_model=List[Track])
def tracks():
    return data


@app.get('/tracks/{track_id}/', response_model=Union[Track, str])
def track(track_id: int, response: Response):
    # find the track with the given ID, or None if it does not exist
    track = next(
        (track for track in data if track["id"] == track_id), None
    )
    if track is None:
        # if a track with given ID doesn't exist, set 404 code and return string
        response.status_code = 404
        return "Track not found"
    return track


@app.post("/tracks/", response_model=Track, status_code=201)
def create_track(track: Track):
    track_dict = track.dict()
    
    # assign track next sequential ID
    track_dict['id'] = max(data, key=lambda x: x['id']).get('id') + 1
    
    # append the track to our data and return 201 response with created resource
    data.append(track_dict)
    return track_dict


@app.put("/tracks/{track_id}", response_model=Union[Track, str])
def update_track(track_id: int, updated_track: Track, response: Response):

    track = next(
        (track for track in data if track["id"] == track_id), None
    )

    if track is None:
        # if a track with given ID doesn't exist, set 404 code and return string
        response.status_code = 404
        return "Track not found"
    
    # update the track data
    for key, val in updated_track.dict().items():
        if key != 'id': # don't reset the ID
            track[key] = val
    return track

@app.delete("/tracks/{track_id}")
def delete_track(track_id: int, response: Response):

    # get the index of the track to delete
    delete_index = next(
        (idx for idx, track in enumerate(data) if track["id"] == track_id), None
    )

    if delete_index is None:
        # if a track with given ID doesn't exist, set 404 code and return string
        response.status_code = 404
        return "Track not found"
    
    # delete the track from the data, and return empty 200 response
    del data[delete_index]
    return Response(status_code=200)