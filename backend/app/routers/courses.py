from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user, require_verified_member
from app.models import Campus, Course, StudentCourse, User
from app.schemas import CourseCreateIn

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("")
def list_courses(campus_slug: str, db: Session = Depends(get_db)):
    campus = db.scalar(select(Campus).where(Campus.slug == campus_slug))
    if not campus:
        raise HTTPException(404, "Campus not found")
    return [
        {"id": c.id, "code": c.code, "name": c.name, "semester": c.semester}
        for c in db.scalars(
            select(Course).where(Course.campus_id == campus.id).order_by(Course.semester, Course.code)
        ).all()
    ]


@router.get("/mine")
def my_courses(campus_slug: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(Course).join(StudentCourse, StudentCourse.course_id == Course.id).where(StudentCourse.user_id == user.id)
    if campus_slug:
        q = q.join(Campus, Campus.id == Course.campus_id).where(Campus.slug == campus_slug)
    return [
        {"id": c.id, "code": c.code, "name": c.name, "semester": c.semester, "campus_slug": c.campus.slug}
        for c in db.scalars(q.order_by(Course.semester, Course.code)).all()
    ]


@router.post("/{course_id}/enroll")
def enroll(course_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    require_verified_member(course.campus.slug, user, db)
    exists = db.scalar(select(StudentCourse).where(
        StudentCourse.user_id == user.id,
        StudentCourse.course_id == course.id,
    ))
    if not exists:
        db.add(StudentCourse(user_id=user.id, course_id=course.id))
        db.commit()
    return {"course_id": course_id, "enrolled": True}


@router.delete("/{course_id}/enroll")
def unenroll(course_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.scalar(select(StudentCourse).where(
        StudentCourse.user_id == user.id,
        StudentCourse.course_id == course_id,
    ))
    if row:
        db.delete(row)
        db.commit()
    return {"course_id": course_id, "enrolled": False}
