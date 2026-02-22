# PROJECT CHARTER – FULL SYSTEM CONSTITUTION
Autonomous-Trading-System
Version 1.0

---

# 1. PROJECT IDENTITY

This is not a hobby bot project.

This is a long-term systems engineering project whose objective is to design, build, and evolve a modular autonomous trading system capable of operating continuously and generating sustainable profits over time.

This project prioritizes:

- Structure
- Modularity
- Clean architecture
- Reversibility
- Phase discipline
- Long-term scalability
- System survivability

Speed is secondary to structural integrity.

---

# 2. CORE OBJECTIVE

Build a modular, autonomous, evolving trading system capable of:

- Testing market strategies (crypto + prediction markets)
- Executing trades automatically
- Logging all activity
- Evaluating performance over time
- Improving based on data
- Allocating capital intelligently
- Operating 24/7 with minimal human intervention
- Eventually producing real, sustainable profits

---

# 3. LONG-TERM VISION

The final system will include:

- A reusable signal engine
- Multiple execution engines (crypto, Polymarket, arbitrage)
- A risk management layer
- A logging & performance intelligence layer
- A capital allocation engine
- Regime detection logic
- Strategy evolution framework

Execution venue must be modular.
Signal logic must be portable.
No single exchange dependency may control architecture.

---

# 4. MASTER ROADMAP (LOCKED PHASES)

## Phase 1 – Execution Engine Stabilization
- Stabilize Freqtrade as crypto execution engine
- Understand trade lifecycle
- Confirm logging + database structure
- Run dry-run continuously
- No architecture refactor
- No premature complexity

## Phase 2 – Modular Strategy Architecture
- Extract signal logic from execution
- Create reusable core modules
- Ensure strategy logic is execution-agnostic

## Phase 3 – Performance Intelligence Layer
- Log regime data
- Evaluate performance by environment
- Identify strategy failure conditions
- Enable data-driven refinement

## Phase 4 – Capital Allocation Layer
- Support multiple strategies
- Dynamic capital allocation
- Drawdown control logic

## Phase 5 – Polymarket Execution Engine
- Build Polymarket-native executor
- Integrate shared signal engine
- Maintain architectural separation from crypto

## Phase 6 – Arbitrage Engine
- Multi-venue price monitoring
- Spread detection
- Execution routing logic
- Risk-balanced arbitrage allocation

Phases may not be skipped.

---

# 5. ARCHITECTURAL PRINCIPLES

The system must remain layered:

1. Signal Layer
2. Risk Layer
3. Execution Layer
4. Logging Layer
5. Performance Analysis Layer
6. Capital Allocation Layer

No cross-layer contamination.

Execution engines are workers.
Core system is the brain.

Freqtrade is an execution engine only.
It is not the master system.

Polymarket will be a separate execution engine.
It will not be forced into Freqtrade architecture.

---

# 6. FREQTRADE POLICY

- Freqtrade core files must never be modified.
- Only user_data and integration layers may be customized.
- Freqtrade is treated as an external dependency.
- Upgrade compatibility must be preserved.

---

# 7. POLYMARKET POLICY

- Polymarket is fundamentally different from centralized exchanges.
- It requires its own execution adapter.
- It must not be forced into CCXT architecture.
- Shared signal logic will be imported from core modules.

---

# 8. ARBITRAGE POLICY

Arbitrage is a separate strategy class.

Types considered:
- Cross-exchange crypto arbitrage
- Crypto ↔ prediction market arbitrage
- Intra-market inefficiency detection

Arbitrage logic must not contaminate trend strategy logic.

---

# 9. DEVELOPMENT DISCIPLINE RULES

1. No chaos.
2. No impulsive changes.
3. No premature AI/ML complexity.
4. No architectural shortcuts.
5. No mixing phases.
6. Every major decision must be documented.
7. Every change must be reversible when possible.
8. Repository documentation is law.
9. Complexity must be justified before introduction.
10. If unsure, do not proceed.

---

# 10. USER CONSTRAINTS

The project owner:

- Has no coding experience.
- Is not comfortable with terminal.
- Requires step-by-step instructions.
- Requires clarity and precision.
- Needs structure and guidance.
- Must not be overwhelmed with assumptions.

All instructions must be beginner-safe.

---

# 11. AI OPERATING ROLE

The AI acts as:

- Strategic Architect
- Systems Product Manager
- Structural Enforcer
- Phase Discipline Monitor
- Risk & Complexity Evaluator
- Clean Architecture Guardian

The AI does NOT:

- Encourage chaos
- Skip phases
- Introduce premature complexity
- Modify third-party cores impulsively

---

# 12. MEMORY PROTOCOL

AI memory is not persistent.

Therefore:

- Repository documentation is the permanent memory.
- Each session must begin with:
  - Current Phase
  - Last Change
  - Current Goal
  - Constraints
  - Blockers
- If it is not written in the repo, it does not exist.

---

# 13. LOGGING & EVOLUTION GOAL

The long-term system must:

- Log entry conditions
- Log exit conditions
- Log regime characteristics
- Track expectancy by regime
- Detect performance decay
- Adapt capital allocation
- Disable failing strategies automatically

The system must evolve based on data.

---

# 14. SUCCESS CRITERIA

Short-Term:
- Stable crypto execution engine
- Clean modular repository
- Clear roadmap enforcement

Mid-Term:
- Portable signal engine
- Strategy evaluation layer
- Capital allocation logic

Long-Term:
- Profitable autonomous trading
- Multi-executor architecture
- Self-improving system
- Minimal manual intervention

---

This document governs all decisions.
Deviation requires explicit justification and documentation.
