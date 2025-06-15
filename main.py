from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import create_engine
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

DATABASE_URL = "postgresql://tododb_psm0_user:52rbYsY71itHjOYLB3uTnEMsHjsBOuRI@dpg-cvh8dj5ds78s73e2mti0-a/tododb_psm0"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# Database model
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, default="")
    is_done = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# Pydantic models
class TaskCreate(BaseModel):
    title: str
    description: str = ""

class TaskRead(TaskCreate):
    id: int
    is_done: bool

    class Config:
        orm_mode = True

class TaskUpdate(BaseModel):
    title: str
    description: str = ""
    is_done: bool


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD operations
@app.post("/tasks/", response_model=TaskRead)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(title=task.title, description=task.description)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=list[TaskRead])
def read_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()

@app.get("/tasks/{task_id}", response_model=TaskRead)
def read_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db_task.title = task.title
    db_task.description = task.description
    db_task.is_done = task.is_done

    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"detail": "Task deleted"}