# Engineering Optimisation: Multi-Objective Paper Helicopter Design

## Project Overview

This project explores the application of **engineering optimisation techniques** to the design of a paper helicopter, investigating the trade-off between **manufacturing cost (£)** and **falling velocity (m/s)**.

Using computational optimisation and mathematical analysis, the project evaluates candidate helicopter designs to identify optimal configurations that balance economic efficiency with aerodynamic performance.

The optimisation problem is formulated as a **multi-objective optimisation problem**, with a Pareto-front representation used to visualise the trade-offs between competing engineering objectives.

## Technology Stack

- **Python** – Computational modelling, optimisation workflows and data analysis.
- **NumPy** – Numerical computation, mathematical operations and manipulation of optimisation data.
- **pymoo** – Multi-objective optimisation framework for evaluating candidate solutions and generating Pareto-optimal solutions.
- **Mathematical Optimisation** – Application of constrained optimisation principles and engineering design analysis.
- **KKT Conditions** – Karush–Kuhn–Tucker conditions for analysing constrained optimisation problems and understanding optimality conditions.

## Pareto Front

![Pareto front showing cost versus falling velocity](pareto_front.png)

*Figure 1. Pareto front illustrating the relationship between cost (£) and falling velocity (m/s) across candidate paper helicopter designs.*

### How to interpret the plot

The Pareto front represents the set of **non-dominated solutions** across the two engineering objectives:

- **Cost (x-axis):** Lower values are preferable when minimising manufacturing expenditure.
- **Falling velocity (y-axis):** Lower values are preferable when improving the helicopter's descent performance.
- **Trade-off:** Moving from left to right increases cost while reducing falling velocity. Cheaper designs therefore tend to have higher falling velocities, whereas achieving slower descent may require additional material or design expenditure.
- **Design selection:** There is no universally optimal solution. The preferred configuration depends on the engineering constraints, budget and desired aerodynamic performance.

A solution is Pareto-dominated if another solution performs at least as well in both objectives and strictly better in at least one. Solutions on the Pareto front are non-dominated, meaning that improving one objective requires sacrificing performance in the other, within the evaluated candidate solutions.

## Engineering Optimisation Objectives

The project formulates a two-objective optimisation problem:

1. **Minimise manufacturing cost (£).**
2. **Minimise falling velocity (m/s).**

The optimisation process investigates how changes in the paper helicopter's design influence its overall performance and cost.

The use of multi-objective optimisation enables competing engineering requirements to be evaluated systematically rather than optimising for a single performance measure.

### Mathematical Optimisation and KKT Conditions

The project incorporates constrained engineering optimisation principles, including the **Karush–Kuhn–Tucker (KKT) conditions**.

KKT conditions provide a mathematical framework for analysing constrained optimisation problems by considering:

- Stationarity of the objective function.
- Primal feasibility of the design constraints.
- Dual feasibility of the Lagrange multipliers.
- Complementary slackness.

These conditions help establish the theoretical foundations for identifying optimal solutions under engineering constraints.

## Collaborative Engineering Approach

This project was undertaken through **team-based engineering design and optimisation**.

The collaborative approach involved applying mathematical modelling, computational methods and engineering analysis to investigate the paper helicopter's design and performance.

Key areas of collaboration included:

- Engineering problem formulation and identification of optimisation objectives.
- Computational modelling and numerical analysis using Python and NumPy.
- Application of the pymoo framework for multi-objective optimisation.
- Mathematical investigation of constrained optimisation and KKT conditions.
- Interpretation of Pareto-optimal solutions to support engineering design decisions.

The project demonstrates the integration of computational engineering, applied mathematics and collaborative problem-solving.

## Repository Figure

Ensure `pareto_front.png` is stored in the same directory as this `README.md` so that the visualisation renders correctly on GitHub.

This README will be updated as the project progresses towards its final submission, including the specific optimisation algorithm, design variables, constraints, experimental dataset and instructions for reproducing the results.

## Key Skills Demonstrated

- Engineering Optimisation
- Multi-Objective Optimisation
- Pareto-Front Analysis
- Constrained Optimisation
- KKT Optimality Conditions
- Python Programming
- NumPy Numerical Computing
- pymoo Optimisation Framework
- Engineering Modelling and Analysis
- Teamwork and Collaborative Problem-Solving
