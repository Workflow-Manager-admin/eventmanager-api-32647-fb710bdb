from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Field, SQLModel, Session, create_engine, select
from typing import Optional, List
from datetime import datetime


# Database setup
DATABASE_URL = "sqlite:///./events.db"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# Models and Schemas


class EventBase(SQLModel):
    title: str = Field(
        ..., description="Title of the event", max_length=255
    )
    description: Optional[str] = Field(
        None, description="Detailed description of the event"
    )
    start_time: datetime = Field(
        ..., description="Start time of the event in ISO8601 format"
    )
    end_time: datetime = Field(
        ..., description="End time of the event in ISO8601 format"
    )
    location: Optional[str] = Field(
        None, description="Location where the event is held"
    )


class Event(EventBase, table=True):
    id: Optional[int] = Field(
        default=None, primary_key=True, description="Unique event identifier"
    )


class EventCreate(EventBase):
    pass


class EventUpdate(SQLModel):
    title: Optional[str] = Field(
        None, description="Title of the event", max_length=255
    )
    description: Optional[str] = Field(
        None, description="Detailed description of the event"
    )
    start_time: Optional[datetime] = Field(
        None, description="Start time of the event in ISO8601 format"
    )
    end_time: Optional[datetime] = Field(
        None, description="End time of the event in ISO8601 format"
    )
    location: Optional[str] = Field(
        None, description="Location where the event is held"
    )


class EventRead(EventBase):
    id: int = Field(..., description="Unique event identifier")

# Dependency


def get_session():
    with Session(engine) as session:
        yield session


# FastAPI app
app = FastAPI(
    title="Event Manager API",
    description="API backend for managing events: create, update, delete, list, and detail.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Events", "description": "Event CRUD operations"},
    ],
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create the database table(s) on startup
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# PUBLIC_INTERFACE
@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint to confirm the API is running."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.post(
    "/events/",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an Event",
    tags=["Events"],
    responses={201: {"description": "Event created successfully."}},
)
def create_event(event: EventCreate, session: Session = Depends(get_session)):
    """Create a new event with the provided details."""
    db_event = Event.from_orm(event)
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


# PUBLIC_INTERFACE
@app.get(
    "/events/",
    response_model=List[EventRead],
    summary="List All Events",
    tags=["Events"],
    responses={200: {"description": "List of all events."}},
)
def list_events(session: Session = Depends(get_session)):
    """Get a list of all events."""
    events = session.exec(select(Event)).all()
    return events


# PUBLIC_INTERFACE
@app.get(
    "/events/{event_id}",
    response_model=EventRead,
    summary="Get Event Details",
    tags=["Events"],
    responses={
        200: {"description": "Event details found."},
        404: {"description": "Event not found."},
    },
)
def get_event(event_id: int, session: Session = Depends(get_session)):
    """Retrieve details of an event by its ID."""
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


# PUBLIC_INTERFACE
@app.put(
    "/events/{event_id}",
    response_model=EventRead,
    summary="Update an Event",
    tags=["Events"],
    responses={
        200: {"description": "Event updated successfully."},
        404: {"description": "Event not found."},
    },
)
def update_event(
    event_id: int, event_update: EventUpdate, session: Session = Depends(get_session)
):
    """Update an existing event by its ID."""
    db_event = session.get(Event, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = event_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


# PUBLIC_INTERFACE
@app.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an Event",
    tags=["Events"],
    responses={
        204: {"description": "Event deleted successfully."},
        404: {"description": "Event not found."},
    },
)
def delete_event(event_id: int, session: Session = Depends(get_session)):
    """Delete an event by its ID."""
    db_event = session.get(Event, event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    session.delete(db_event)
    session.commit()
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
