# CampusCart — Technical Project Brief

## Problem

Students frequently need low-cost, local access to textbooks, electronics, hostel essentials and course materials. Generic marketplaces lack campus-specific discovery, trust signals and structured handoff workflows.

## Technical contribution

CampusCart implements a campus-scoped exchange lifecycle: authentication and OTP → campus selection → listing → discovery/recommendation → offer/swap → payment → pickup scheduling → handoff → completion → review/reputation.

## Engineering focus

The system demonstrates relational state management, API authorization, provider verification, asynchronous infrastructure, rate limiting, observable requests, database migrations and testable transaction invariants. The codebase also includes an explicit evaluation plan for Smart Swap/Wanted recommendations rather than presenting unvalidated recommendation scores.

## What is not claimed

The project should not claim that a generic Gmail or phone OTP proves university enrollment. In the current prototype, OTP proves contact ownership and campus membership is a separate application-level choice. Production deployment would need an institution-verification policy appropriate to the campuses served.
