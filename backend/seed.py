
from datetime import date, datetime, timedelta
from decimal import Decimal
import os
from sqlalchemy import select
from app.db import Base, engine, SessionLocal
from app.models import Address, Campus, CampusMember, Course, Listing, ListingImage, PickupLocation, SellerProfile, User, WantedPost
from app.campus_models import CampusDomain
from app.security import hash_password, hash_value

SEED_CAMPUS_NAME = os.getenv("SEED_CAMPUS_NAME", "Pune Tech University")
SEED_CAMPUS_SLUG = os.getenv("SEED_CAMPUS_SLUG", "pune-tech")
SEED_CITY = os.getenv("SEED_CITY", "Pune")
SEED_STATE = os.getenv("SEED_STATE", "Maharashtra")
SEED_PINCODE = os.getenv("SEED_PINCODE", "411007")
SEED_EMAIL_DOMAIN = os.getenv("SEED_EMAIL_DOMAIN", "ptu.edu")
SEED_SELLER_EMAIL = os.getenv("SEED_SELLER_EMAIL", f"seller@{SEED_EMAIL_DOMAIN}")
SEED_BUYER_EMAIL = os.getenv("SEED_BUYER_EMAIL", f"buyer@{SEED_EMAIL_DOMAIN}")
SEED_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@campuscart.local")
SEED_SELLER_PASSWORD = os.getenv("SEED_SELLER_PASSWORD", "SellerPass123")
SEED_BUYER_PASSWORD = os.getenv("SEED_BUYER_PASSWORD", "BuyerPass123")
SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "AdminPass123")

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campus = db.scalar(select(Campus).where(Campus.slug == SEED_CAMPUS_SLUG))
        if not campus:
            campus = Campus(
                name=SEED_CAMPUS_NAME, slug=SEED_CAMPUS_SLUG, city=SEED_CITY, state=SEED_STATE, pincode=SEED_PINCODE,
                email_domain=SEED_EMAIL_DOMAIN, description="A student-first campus marketplace for books, electronics, notes, and everyday essentials.",
                current_semester="Semester 5", semester_start=date.today() - timedelta(days=45), semester_end=date.today() + timedelta(days=70)
            )
            db.add(campus); db.flush()
        # Keep the legacy field for compatibility, but store approved domains in their own table.
        if not db.scalar(select(CampusDomain).where(CampusDomain.campus_id == campus.id, CampusDomain.domain == campus.email_domain)):
            if campus.email_domain:
                db.add(CampusDomain(campus_id=campus.id, domain=campus.email_domain, active=True))

        if not db.scalar(select(PickupLocation).where(PickupLocation.campus_id == campus.id)):
            for name, address, landmark in [
                ("Main Library", f"{SEED_CAMPUS_NAME}, {SEED_CITY}, {SEED_STATE}", "Near main entrance"),
                ("Main Gate", f"{SEED_CAMPUS_NAME}, {SEED_CITY}, {SEED_STATE}", "Security desk"),
                ("Student Centre", f"{SEED_CAMPUS_NAME}, {SEED_CITY}, {SEED_STATE}", "Ground floor"),
                ("Hostel A", f"{SEED_CAMPUS_NAME} Hostel A, {SEED_CITY}, {SEED_STATE}", "Reception"),
            ]:
                db.add(PickupLocation(campus_id=campus.id, name=name, address=address, landmark=landmark))
        user = db.scalar(select(User).where(User.email == SEED_SELLER_EMAIL))
        if not user:
            user = User(name="Alex Verma", email=SEED_SELLER_EMAIL, phone="+919999999999", password_hash=hash_password(SEED_SELLER_PASSWORD),
                        role="student", email_verified=True, phone_verified=True)
            db.add(user); db.flush()
        member = db.scalar(select(CampusMember).where(CampusMember.campus_id == campus.id, CampusMember.user_id == user.id))
        if not member:
            db.add(CampusMember(campus_id=campus.id, user_id=user.id, student_id_hash=hash_value(f"{SEED_CAMPUS_SLUG}-DEMO-001"),
                                verified=True, verification_method="institutional_email", verified_at=datetime.now()))
        seller = user.seller_profile
        if not seller:
            seller = SellerProfile(user_id=user.id, display_name="Alex Verma", bio="Student seller • books, electronics and useful campus finds.",
                                   verified=True, reputation_score=Decimal("86.50"), completed_orders=17, response_rate=Decimal("96.00"))
            db.add(seller); db.flush()

        buyer = db.scalar(select(User).where(User.email == SEED_BUYER_EMAIL))
        if not buyer:
            buyer = User(name="Rahul Mehta", email=SEED_BUYER_EMAIL, phone="+918888888888", password_hash=hash_password(SEED_BUYER_PASSWORD),
                         role="student", email_verified=True, phone_verified=True)
            db.add(buyer); db.flush()
        buyer_member = db.scalar(select(CampusMember).where(CampusMember.campus_id == campus.id, CampusMember.user_id == buyer.id))
        if not buyer_member:
            db.add(CampusMember(campus_id=campus.id, user_id=buyer.id, student_id_hash=hash_value(f"{SEED_CAMPUS_SLUG}-DEMO-002"),
                                verified=True, verification_method="institutional_email", verified_at=datetime.now()))
        # Development admin account used to manage campuses and verification requests.
        admin = db.scalar(select(User).where(User.email == SEED_ADMIN_EMAIL))
        if not admin:
            admin = User(
                name="CampusCart Admin",
                email=SEED_ADMIN_EMAIL,
                password_hash=hash_password(SEED_ADMIN_PASSWORD),
                role="admin",
                email_verified=True,
                phone_verified=True,
            )
            db.add(admin)

        buyer_seller = buyer.seller_profile
        if not buyer_seller:
            buyer_seller = SellerProfile(user_id=buyer.id, display_name="Rahul Mehta", bio="Student seller • notes and campus essentials.",
                                         verified=True, reputation_score=Decimal("72.00"), completed_orders=3, response_rate=Decimal("88.00"))
            db.add(buyer_seller); db.flush()

        if not db.scalar(select(Address).where(Address.user_id == user.id)):
            db.add(Address(user_id=user.id, label="Home", line1="12 College Road", locality="Campus Area", city=SEED_CITY, state=SEED_STATE,
                           pincode="411038", landmark="Near the main junction", is_default=True))
        if not db.scalar(select(Address).where(Address.user_id == buyer.id)):
            db.add(Address(user_id=buyer.id, label="Hostel", line1=f"Hostel B, {SEED_CAMPUS_NAME}", locality="Campus Area", city=SEED_CITY, state=SEED_STATE,
                           pincode="411005", landmark="Hostel B reception", is_default=True))
        if not db.scalar(select(Course).where(Course.campus_id == campus.id)):
            courses = [
                ("CS301","Operating Systems","Semester 5"), ("CS302","Database Systems","Semester 5"),
                ("CS303","Computer Networks","Semester 5"), ("MA205","Engineering Mathematics","Semester 5")
            ]
            for code, name, sem in courses: db.add(Course(campus_id=campus.id, code=code, name=name, semester=sem))
        db.flush()
        if not db.scalar(select(Listing).where(Listing.seller_id == seller.id)):
            items = [
                ("Engineering Mathematics","Books","good",Decimal("450"),"/products/math.svg","Negotiable", "Main Library", "Near main entrance","0.3"),
                ("Scientific Calculator","Academic Supplies","good",Decimal("380"),"/products/calculator.svg","Negotiable", "Hostel A","Reception","0.7"),
                ("iPhone 12","Electronics","good",Decimal("22000"),"/products/phone.svg","", "Main Gate","Security desk","1.1"),
                ("Hostel Study Chair","Hostel Essentials","good",Decimal("1200"),"/products/chair.svg","Negotiable", "Hostel B","Common room","0.9"),
                ("MacBook Air M1","Electronics","like-new",Decimal("42000"),"/products/laptop.svg","", "Kothrud","Public meetup only","3.2"),
                ("Lab Coat","Clothing","good",Decimal("500"),"/products/coat.svg","Negotiable", "Hostel C","Reception","1.2"),
                ("Study Table","Furniture","good",Decimal("1500"),"/products/table.svg","Negotiable", "Hostel B","Common room","0.8"),
                ("Wireless Earbuds","Electronics","like-new",Decimal("1100"),"/products/earbuds.svg","Negotiable", "Student Centre","Ground floor","0.4"),
            ]
            for title, cat, cond, price, img, negotiable, area, landmark, dist in items:
                listing = Listing(campus_id=campus.id, seller_id=seller.id, title=title, category=cat, condition=cond,
                                  price=price, description=f"{title} in {cond.replace('-', ' ')} condition. Campus pickup available.",
                                  pickup_area=area, pickup_landmark=landmark, distance_km=Decimal(dist), status="active")
                db.add(listing); db.flush()
                db.add(ListingImage(listing_id=listing.id, url=img, alt=title, sort_order=0))
        if not db.scalar(select(Listing).where(Listing.seller_id == buyer_seller.id)):
            buyer_listing = Listing(campus_id=campus.id, seller_id=buyer_seller.id, title="Data Structures Notes", category="Books",
                                    condition="good", price=Decimal("220"), description="Clean semester notes with solved examples.",
                                    pickup_area="Student Centre", pickup_landmark="Ground floor", distance_km=Decimal("0.5"), status="active")
            db.add(buyer_listing); db.flush()
            db.add(ListingImage(listing_id=buyer_listing.id, url="/products/notes.svg", alt="Data Structures Notes", sort_order=0))
        if not db.scalar(select(WantedPost).where(WantedPost.campus_id == campus.id)):
            for title, cat, bmin, bmax in [
                ("DBMS textbook","Books",Decimal("300"),Decimal("600")),
                ("Scientific Calculator","Academic Supplies",Decimal("300"),Decimal("500")),
                ("24-inch monitor","Electronics",Decimal("3000"),Decimal("7000")),
                ("Lab Coat","Clothing",Decimal("250"),Decimal("600")),
            ]:
                db.add(WantedPost(campus_id=campus.id, user_id=user.id, title=title, category=cat, budget_min=bmin, budget_max=bmax,
                                  needed_by=date.today()+timedelta(days=12)))
        db.commit()
        print("CampusCart seed complete.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
