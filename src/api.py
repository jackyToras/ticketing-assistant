import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.auth import create_access_token, get_current_user, hash_password, verify_password
from src.database import Base, engine, get_db
from src.decision import DecisionServiceError, create_decision
from src.models import Decision, Ticket, User
from src.schemas import DecisionResponse, LoginRequest, RegisterRequest, TicketCreate, TicketResponse, TokenResponse, UserResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Support Ticket Decision API", version="0.1.0", lifespan=lifespan)


def serialize_ticket(ticket: Ticket) -> TicketResponse:
    decision = None
    if ticket.decision:
        decision = DecisionResponse(
            action=ticket.decision.action,
            reason=ticket.decision.reason,
            confidence=ticket.decision.confidence,
            sources=json.loads(ticket.decision.sources),
            created_at=ticket.decision.created_at,
        )
    return TicketResponse(
        id=ticket.id,
        message=ticket.message,
        order_value_inr=ticket.order_value_inr,
        days_since_delivery=ticket.days_since_delivery,
        days_since_dispatch=ticket.days_since_dispatch,
        product_type=ticket.product_type,
        opened_status=ticket.opened_status,
        order_status=ticket.order_status,
        created_at=ticket.created_at,
        decision=decision,
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return TokenResponse(access_token=create_access_token(user.id))


@app.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/tickets", response_model=list[TicketResponse])
def list_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tickets = db.scalars(
        select(Ticket).where(Ticket.user_id == current_user.id).options(selectinload(Ticket.decision)).order_by(Ticket.created_at.desc())
    ).all()
    return [serialize_ticket(ticket) for ticket in tickets]


@app.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        generated_decision = create_decision(payload)
    except DecisionServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    ticket = Ticket(user_id=current_user.id, **payload.model_dump())
    db.add(ticket)
    db.flush()
    db.add(
        Decision(
            ticket_id=ticket.id,
            action=generated_decision.action,
            reason=generated_decision.reason,
            confidence=generated_decision.confidence,
            sources=json.dumps(generated_decision.sources),
        )
    )
    db.commit()
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket.id).options(selectinload(Ticket.decision)))
    return serialize_ticket(ticket)


@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.user_id == current_user.id).options(selectinload(Ticket.decision))
    )
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return serialize_ticket(ticket)
