# CampusCart — Project Overview

## Problem

Students often need low-cost access to textbooks, electronics and hostel items close to campus. General marketplaces provide discovery, but they do not naturally handle campus membership, pickup coordination or student-to-student handoff.

CampusCart keeps those pieces together in a single web application.

## Main user journeys

A buyer can discover a listing, message the seller, make or receive an offer, pay where required, schedule pickup and complete the handoff. Sellers can create and edit listings, upload photos, receive offers and track transactions.

The same application also supports Wanted posts, Smart Swap, Lost & Found, course-tagged listings, saved items, notifications and moderation.

## Architecture

The browser talks to a FastAPI application. PostgreSQL owns durable business state. Redis is used for rate limits, cache entries and token revocation, while the worker handles asynchronous jobs. Listing photos can be stored locally during development or in an S3-compatible object store in production.

## Authentication

Users verify control of an email address or Indian phone number with an OTP. The OTP is not treated as proof of university enrollment. Campus membership is handled separately through institutional-domain checks and administrator review.

## Transaction lifecycle

A normal paid transaction moves through explicit states such as awaiting payment, paid, pickup scheduled, waiting for handoff and completed. Cancellation and refund checks are enforced by the backend. Handoff uses a short buyer-provided code and two-sided confirmation.

Swap transactions use the same pickup and handoff machinery but do not require a normal payment step. Completing a swap closes both exchanged listings.

## External services

Provider integrations are isolated behind service modules so the application can run locally without live accounts. Razorpay is used for payment processing when enabled; Twilio Verify and SMTP handle optional OTP delivery; S3-compatible storage handles production media.

## Design priorities

1. Keep ownership and transaction rules on the server.
2. Prefer explicit state transitions over implicit flags.
3. Keep private addresses out of public listing data.
4. Make local development possible without paid external services.
5. Keep provider-specific code separate from the marketplace domain.

## Development notes

The seed data is intentionally small. The recommendation layer starts with deterministic rules and has an offline evaluator for later measurement once there is enough real interaction data.
