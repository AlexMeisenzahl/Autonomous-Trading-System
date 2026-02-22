# PROJECT CHARTER
Autonomous-Trading-System

---

## 1. Core Objective

Build a modular, autonomous, evolving trading system capable of:

- Testing market strategies (crypto and prediction markets)
- Executing trades automatically
- Logging all activity
- Evaluating performance over time
- Improving strategies systematically
- Running continuously with minimal human intervention
- Eventually generating real, sustainable profits

This is a long-term personal systems engineering project.

---

## 2. Long-Term Vision

Develop autonomous bots that:

- Operate 24/7
- Are modular and upgradeable
- Separate signal logic from execution logic
- Support multiple execution venues (crypto, Polymarket, arbitrage)
- Log performance in a structured way
- Adapt based on data
- Allocate capital intelligently
- Require minimal manual input once deployed

The system must evolve, not remain static.

---

## 3. Current Phase

Phase 1 – Execution Engine Stabilization

Current focus:
- Stabilize Freqtrade as crypto execution engine
- Understand lifecycle of trades
- Confirm logging, database, and UI behavior
- Run dry-run trading continuously
- No architectural refactors yet

No premature complexity.

---

## 4. Development Principles (Non-Negotiable)

1. No chaos.
2. No impulsive changes.
3. No modifying third-party engine core files.
4. No mixing architectural layers.
5. No premature AI or optimization complexity.
6. Every major decision must be documented.
7. Every change must be reversible unless intentionally permanent.
8. Clean modular design is prioritized over speed.
9. Phase discipline must be enforced.
10. The repository documentation is the single source of truth.

---

## 5. Architectural Principles

The system must be layered:

Signal Layer
Risk Layer
Execution Layer
Logging Layer
Performance Analysis Layer
Capital Allocation Layer

These layers must remain separated.

Execution engines (crypto, Polymarket, arbitrage) must be modular workers.

Core strategy logic must eventually live independently of execution engines.

---

## 6. Constraints

- The project owner has no coding experience.
- Instructions must be clear, detailed, and step-by-step.
- Terminal instructions must be explicit and beginner-safe.
- No assumptions of prior programming knowledge.
- Changes must be explained clearly before being executed.

---

## 7. AI Role Definition

The AI operates as:

- Strategic Architect
- Systems Product Manager
- Structure Enforcer
- Complexity Gatekeeper
- Risk Evaluator
- Phase Discipline Monitor

The AI does NOT:

- Encourage chaotic experimentation
- Skip architectural planning
- Modify third-party core systems impulsively
- Introduce unnecessary complexity

---

## 8. Documentation Protocol

Before each work session, the following must be identified:

- Current Phase
- Last Change Made
- Current Goal
- Known Constraints
- Active Blockers

If it is not written in the repository, it does not exist.

---

## 9. Success Criteria

Short-term:
- Stable execution engine
- Clean modular repository
- Clear roadmap

Mid-term:
- Reusable signal architecture
- Performance logging and evaluation layer

Long-term:
- Profitable autonomous strategies
- Multi-executor architecture
- Continuous improvement framework

---

This document governs all future architectural and development decisions.
