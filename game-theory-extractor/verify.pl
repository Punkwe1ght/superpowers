%% verify.pl - Verification queries for game theory knowledge base
%% Load with: ?- consult('verify.pl').

%% verify_knowledge_base is det
%% Entry point for Phase 2. Run all verification checks.
verify_knowledge_base :-
    format('~n=== Undefined Concepts ===~n'),
    forall(undefined_concept(C), format('  ~w~n', [C])),
    format('~n=== Orphan Concepts ===~n'),
    forall(orphan_concept(C), format('  ~w~n', [C])),
    format('~n=== Duplicate Concepts ===~n'),
    forall(duplicate_concept(C, Ps), format('  ~w: pages ~w~n', [C, Ps])),
    format('~n=== Invalid Relations ===~n'),
    forall(invalid_relation(C1, C2, R), format('  ~w -> ~w: ~w~n', [C1, C2, R])),
    format('~n=== Summary ===~n'),
    count_facts.

%% undefined_concept(-C) is nondet
%% C appears in relates/3 but lacks a concept/3 definition.
%% Uses distinct/2 to avoid duplicate results when C appears in both positions.
undefined_concept(C) :-
    distinct(C, (
        ( relates(C, _, _) ; relates(_, C, _) ),
        \+ concept(C, _, _)
    )).

%% orphan_concept(-C) is nondet
%% C has a definition but no relations. May be valid for foundational concepts.
orphan_concept(C) :-
    concept(C, _, _),
    \+ relates(C, _, _),
    \+ relates(_, C, _).

%% duplicate_concept(-C, -Pages) is nondet
%% C has definitions on multiple pages.
duplicate_concept(C, Pages) :-
    setof(P, D^concept(C, P, D), Pages),
    length(Pages, N),
    N > 1.

%% invalid_relation(-C1, -C2, -R) is nondet
%% R is not a valid relation type.
invalid_relation(C1, C2, R) :-
    relates(C1, C2, R),
    \+ valid_relation_type(R).

%% count_facts is det
%% Print summary counts of all fact types.
count_facts :-
    aggregate_all(count, concept(_, _, _), ConceptCount),
    aggregate_all(count, relates(_, _, _), RelatesCount),
    aggregate_all(count, example(_, _, _), ExampleCount),
    aggregate_all(count, formula(_, _, _), FormulaCount),
    format('  Concepts: ~w~n', [ConceptCount]),
    format('  Relations: ~w~n', [RelatesCount]),
    format('  Examples: ~w~n', [ExampleCount]),
    format('  Formulas: ~w~n', [FormulaCount]),
    Total is ConceptCount + RelatesCount + ExampleCount + FormulaCount,
    format('  Total facts: ~w~n', [Total]).

%% list_concepts is det
%% List all concepts with their page numbers.
list_concepts :-
    format('~n=== All Concepts ===~n'),
    forall(
        concept(C, P, D),
        format('  ~w (p.~w): ~w~n', [C, P, D])
    ).

%% concept_graph is det
%% Show all relationships in a readable format.
concept_graph :-
    format('~n=== Concept Graph ===~n'),
    forall(
        relates(C1, C2, R),
        format('  ~w --[~w]--> ~w~n', [C1, R, C2])
    ).

%% find_concept(+Pattern) is det
%% Find concepts matching a pattern (uses sub_atom for substring match).
find_concept(Pattern) :-
    format('~n=== Concepts matching "~w" ===~n', [Pattern]),
    forall(
        ( concept(C, P, D), atom_string(C, CStr), sub_string(CStr, _, _, _, Pattern) ),
        format('  ~w (p.~w): ~w~n', [C, P, D])
    ).

%% related_to(+Concept) is det
%% Find all concepts related to a given concept.
related_to(Concept) :-
    format('~n=== Related to ~w ===~n', [Concept]),
    format('Outgoing:~n'),
    forall(
        relates(Concept, C2, R),
        format('  --[~w]--> ~w~n', [R, C2])
    ),
    format('Incoming:~n'),
    forall(
        relates(C1, Concept, R),
        format('  ~w --[~w]-->~n', [C1, R])
    ).
