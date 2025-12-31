%% janus_re.pl - Janus Reverse Engineering Skill Prolog Implementation
%% Tests constraint checking against real decompiled code samples

:- dynamic function/3.
:- dynamic calls/3.
:- dynamic returns/2.
:- dynamic reads/3.
:- dynamic writes/3.
:- dynamic arg_flows_to/3.
:- dynamic hypothesis/3.
:- dynamic known_pattern/2.
:- dynamic vuln_hypothesis/3.
:- dynamic requires_type/3.
:- dynamic actual_type/3.
:- dynamic global_key/1.
:- dynamic user_controlled_input/1.
:- dynamic data_flows_base/2.
:- dynamic bounds_check_before/1.
:- dynamic size_validation_before/1.

:- discontiguous has_input/2.

%% What patterns require
requires(aes_encrypt, [key, plaintext]).
requires(aes_decrypt, [key, ciphertext]).
requires(hmac, [key, message]).
requires(hash_md4, [input, output]).
requires(hash_md5, [input, output]).
requires(crypto_operation, [key, data]).
requires(network_io, [socket, buffer]).

%% Detect missing inputs
missing_input(Func, Required) :-
    hypothesis(Func, Purpose, _),
    requires(Purpose, Inputs),
    member(Required, Inputs),
    \+ has_input(Func, Required).

%% Base case: exact semantic match
has_input(Func, Input) :-
    arg_flows_to(Func, _, Input).

%% Flexible matching: structural roles satisfy semantic requirements

%% Struct access satisfies socket for network hypotheses
has_input(Func, socket) :-
    arg_flows_to(Func, _, struct_access),
    hypothesis(Func, network_io, _).

%% Struct access satisfies key for crypto hypotheses
has_input(Func, key) :-
    arg_flows_to(Func, _, struct_access),
    hypothesis(Func, Purpose, _),
    crypto_purpose(Purpose).

%% Helper: crypto-related purposes (keyed operations only)
%% NOTE: Hash functions (hash_md4, hash_md5) are NOT crypto_purpose
%% because they don't require keys - they're one-way functions.
crypto_purpose(aes_encrypt).
crypto_purpose(aes_decrypt).
crypto_purpose(hmac).

%% For hash functions: two unknown params can satisfy input/output
%% (Hash functions just pass data through, less strict than crypto keys)
has_input(Func, input) :-
    hypothesis(Func, Purpose, _),
    is_hash_purpose(Purpose),
    arg_flows_to(Func, N1, unknown),
    arg_flows_to(Func, N2, unknown),
    N1 \= N2.

has_input(Func, output) :-
    hypothesis(Func, Purpose, _),
    is_hash_purpose(Purpose),
    arg_flows_to(Func, N1, unknown),
    arg_flows_to(Func, N2, unknown),
    N1 \= N2.

%% Detect contradictions
contradiction(Func, missing_input(What)) :-
    missing_input(Func, What).

contradiction(Func, type_mismatch(Arg, Expected, Actual)) :-
    hypothesis(Func, Purpose, _),
    requires_type(Purpose, Arg, Expected),
    actual_type(Func, Arg, Actual),
    Expected \= Actual.

contradiction(Func, conflicting_hypotheses(H1, H2)) :-
    hypothesis(Func, H1, _),
    hypothesis(Func, H2, _),
    H1 @< H2,  % Canonical ordering to avoid duplicate pairs
    incompatible(H1, H2).

contradiction(Func, missing_hash_call) :-
    hypothesis(Func, Purpose, _),
    is_hash_purpose(Purpose),
    \+ has_hash_call(Func).

is_hash_purpose(hash_md4).
is_hash_purpose(hash_md5).
is_hash_purpose(crypto_hash).

has_hash_call(Func) :-
    calls(Func, Callee, _),
    is_hash_function(Callee).

is_hash_function('HashMd4').
is_hash_function('HashMd5').
is_hash_function('MD4').
is_hash_function('MD5').
is_hash_function('SHA1').
is_hash_function('SHA256').

%% Symmetric incompatibility check (deterministic with once/1)
incompatible(A, B) :-
    once(( incompatible_(A, B) ; incompatible_(B, A) )).

incompatible_(encrypt, decrypt).
incompatible_(malloc, free).
incompatible_(read_only, writes_memory).

%% Transitive data flow (tabled to prevent cycles)
:- table data_flows/2.

data_flows(A, B) :- data_flows_base(A, B).
data_flows(A, C) :-
    data_flows_base(A, B),
    data_flows(B, C).

%% Vulnerability checking
vuln_reachable(Func) :-
    user_controlled_input(Source),
    data_flows(Source, Func).

vuln_contradicted(Func, bounds_checked) :-
    vuln_hypothesis(Func, buffer_overflow, _),
    bounds_check_before(Func).

vuln_contradicted(Func, size_validated) :-
    vuln_hypothesis(Func, buffer_overflow, _),
    size_validation_before(Func).

mitigation_present(Func, stack_canary) :-
    calls(Func, '__stack_chk_fail', _).

%% Python-friendly query wrappers (return strings, not compound terms)
contradiction_str(Func, CStr) :-
    contradiction(Func, C),
    term_string(C, CStr).

mitigation_str(Func, MStr) :-
    mitigation_present(Func, M),
    term_string(M, MStr).

%% Clear all dynamic facts
clear_facts :-
    retractall(function(_, _, _)),
    retractall(calls(_, _, _)),
    retractall(returns(_, _)),
    retractall(reads(_, _, _)),
    retractall(writes(_, _, _)),
    retractall(arg_flows_to(_, _, _)),
    retractall(hypothesis(_, _, _)),
    retractall(known_pattern(_, _)),
    retractall(vuln_hypothesis(_, _, _)),
    retractall(requires_type(_, _, _)),
    retractall(actual_type(_, _, _)),
    retractall(global_key(_)),
    retractall(user_controlled_input(_)),
    retractall(data_flows_base(_, _)),
    retractall(bounds_check_before(_)),
    retractall(size_validation_before(_)).

%% Test runner
run_test(Name, Setup, Expected) :-
    format('~n─────────────────────────────────────────────────────~n'),
    format('TEST: ~w~n', [Name]),
    format('─────────────────────────────────────────────────────~n'),
    clear_facts,
    call(Setup),
    format('~nFacts asserted. Checking contradictions...~n~n'),
    (   findall(C, (hypothesis(F, _, _), contradiction(F, C)), Contradictions),
        Contradictions \= []
    ->  format('CONTRADICTIONS FOUND:~n'),
        forall(member(Cont, Contradictions), format('  - ~w~n', [Cont]))
    ;   format('No contradictions found.~n')
    ),
    format('~nExpected: ~w~n', [Expected]),
    (   findall(M, (hypothesis(F2, _, _), mitigation_present(F2, M)), Mitigations),
        Mitigations \= []
    ->  format('Mitigations: ~w~n', [Mitigations])
    ;   true
    ).

%% ============================================================
%% TEST CASES FROM DECOMPILE-GHIDRA-100K DATASET
%% ============================================================

%% Test 1: ioabs_tcp_pre_select (network I/O function)
setup_tcp_test :-
    assertz(function(tcp_pre_select, 'ioabs_tcp_pre_select', sig(void, [ptr(int), ptr(int), long]))),
    assertz(arg_flows_to(tcp_pre_select, 1, socket)),   % connection contains socket
    assertz(arg_flows_to(tcp_pre_select, 2, counter)),
    assertz(arg_flows_to(tcp_pre_select, 3, buffer)),   % pollfd is a buffer structure
    assertz(hypothesis(tcp_pre_select, network_io, medium)),
    assertz(known_pattern(tcp_pre_select, pollfd_manipulation)).

%% Test 2: hp3800_fixedpwm (scanner driver - false crypto positive)
setup_scanner_test :-
    assertz(function(hp3800, 'hp3800_fixedpwm', sig(int, [int, int]))),
    assertz(arg_flows_to(hp3800, 1, scantype)),
    assertz(arg_flows_to(hp3800, 2, usb)),
    assertz(calls(hp3800, '__stack_chk_fail', [])),
    assertz(hypothesis(hp3800, crypto_operation, low)),  % False hypothesis!
    assertz(known_pattern(hp3800, hex_constants)),
    assertz(known_pattern(hp3800, loop_structure)).

%% Test 3: GenerateNtPasswordHashHash (real crypto function)
setup_hash_test :-
    assertz(function(hash_func, 'GenerateNtPasswordHashHash', sig(void, [long, long]))),
    assertz(arg_flows_to(hash_func, 1, output)),
    assertz(arg_flows_to(hash_func, 2, input)),
    assertz(calls(hash_func, 'HashMd4', [output, input, 16])),
    assertz(hypothesis(hash_func, hash_md4, high)),
    assertz(known_pattern(hash_func, null_check)),
    assertz(known_pattern(hash_func, fixed_size_16)).

%% Test 4: Crypto function WITHOUT key (should contradict)
setup_bad_crypto_test :-
    assertz(function(bad_crypto, 'encrypt_data', sig(void, [ptr(char)]))),
    assertz(arg_flows_to(bad_crypto, 1, data)),
    % Note: NO key input!
    assertz(hypothesis(bad_crypto, aes_encrypt, medium)),
    assertz(known_pattern(bad_crypto, sbox_lookup)).

%% Test 5: Conflicting hypotheses (should contradict)
setup_conflict_test :-
    assertz(function(confused, 'process_buffer', sig(void, [ptr(char)]))),
    assertz(arg_flows_to(confused, 1, buffer)),
    assertz(hypothesis(confused, encrypt, medium)),
    assertz(hypothesis(confused, decrypt, medium)).  % Can't be both!

%% Run all tests
run_all_tests :-
    format('~n======================================================~n'),
    format('JANUS REVERSE ENGINEERING - PROLOG CONSTRAINT TESTS~n'),
    format('======================================================~n'),

    run_test('TCP Network I/O (should pass)',
             setup_tcp_test,
             'No contradictions - network_io with socket/buffer'),

    run_test('Scanner Driver - False Crypto (should contradict)',
             setup_scanner_test,
             'missing_input(key) - crypto needs key, scanner has scantype/usb'),

    run_test('Password Hash (should pass)',
             setup_hash_test,
             'No contradictions - hash_md4 with input/output and HashMd4 call'),

    run_test('Bad Crypto - Missing Key (should contradict)',
             setup_bad_crypto_test,
             'missing_input(key) - AES needs key'),

    run_test('Conflicting Hypotheses (should contradict)',
             setup_conflict_test,
             'conflicting_hypotheses(encrypt, decrypt)'),

    format('~n======================================================~n'),
    format('TESTS COMPLETE~n'),
    format('======================================================~n~n').

%% Entry point - use 'main' to run once
main :- run_all_tests.
