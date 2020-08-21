---
title: Category theory
created: 2020-05-26
modified: 2020-08-21
datelink: [[2020-05-26]]
type: wiki
summary: 
---
[TOC]


<div id='abstract' markdown='1'>
Category theory attempts to generalize all of mathematics using _categories_.
</div>

# Morphisms
A **morphism** is the generalization of functions to mathematical structures beyond sets.
It is formally defined as a structure-preserving map from one mathematical structure to
another of the same type. For example, in set theory, morphisms are functions, while in
group theory they are group homomorphisms, or linear transformations in linear algebra.

The _arrows_ in category theory are morphisms between the objects in a category.

# Classes
A **class** is a collection of sets whereby all members share a certain property. Classes
are informal structures in standard (ZF) [[Set theory]] (as not all collections
of things are considered sets under ZF axioms). Classes that are not sets are called
_proper classes_, while classes that _are_ sets are called _small classes_. Classes are
useful because they escape some limitations of formally defined sets; in category theory,
they are the containers for objects and morphisms (as seen below).

# Categories
A **category** is a collection of _objects_ linked together with _arrows_ having two basic
properties:

1. The ability to compose arrows associatively (i.e. invariance to the order of
   application)
2. The existence of an identity arrow for each object

Common examples include **Sets** (objects) and (set) functions (arrows), rings and ring
homomorphisms, and topological spaces and continuous maps. Categories generally serve to
represent abstractions of mathematical concepts.

Formally, a category $C$ is defined as consisting of

- A class of objects, denoted $\text{ob}(C)$
- A class of morphisms between objects. Each morphism $f$ has a source object $s$ and
  target object $t$ written $f: s \rightarrow t$. $\text{hom}(s,t)$ refers to the class of
  morphisms from $s$ to $t$. Note that
  $$\text{hom}(C) = \cup_{s,t\in\text{obj}(C)} \text{hom}(s,t)$$
- Morphisms can be composed such that $\text{hom}(a,b) \times \text{hom}(b,c) \rightarrow
  \text{hom}(a,c)$ for objects $a$, $b$, and $c$.

# Table of Common Categories
| Category | Objects                        | Morphisms                                |
| :---     | :---                           | :---                                     |
| Grp      | groups                         | group homomorphisms                      |
| Mag      | magmas                         | magma homomorphisms                      |
| Manp     | smooth manifolds               | p-times continuously differentiable maps |
| Met      | metric spaces                  | short maps                               |
| R-Mod    | R-modules, where R is a ring   | R-module homomorphisms                   |
| Mon      | monoids                        | monoid homomorphisms                     |
| Ring     | rings                          | ring homomorphisms                       |
| Set      | sets                           | functions                                |
| Top      | topological spaces             | ontinuous functions                      |
| Uni      | uniform spaces                 | uniformly continuous functions           |
| VectK    | vector spaces over the field K | K-linear maps                            |

