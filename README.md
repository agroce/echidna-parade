This is an experimental script that uses configuration variance and a common corpus to try to throughly test a smart contract (or multiple contracts) with the Echidna smart-contract fuzzer (https://github.com/crytic/echidna).

It runs Echidna instances in parallel, and uses two basic ideas derived from my research:

- swarm testing (https://agroce.github.io/issta12.pdf)

- test length matters (https://agroce.github.io/ase08.pdf)

In particular, after an initial run to generate low-hanging-fruit easy pickings in terms of coverage, future runs will consist of a number of parallel runs (determined by an --ncores argument or however many cores Python thinks you have!) where each run randomly blacklists some functions (if you have a blacklist already, it's respected and added to), and the sequence length varies, by default between 10 and 300, with a bias towards using the default sequence length of 100 or whatever length you specified.

Usage is almost like Echidna; in fact if you just use the same arguments as to Echidna, it'll probably work.  E.g.,

```
> echidna-parade contract.sol --config config.yaml --contract TEST
```

will likely do something reasonable.  By default "generations" of testing are 5 minutes in length, and the testing runs for an hour.

-----------

Try out the example in the 'examples' directory.  Compare:

```
> echidna-test justlen.sol --config config.yaml --contract TEST
```

vs. what you can get with some knowledge of which functions not to omit from tests, and the same 120 seconds of testing with fast swarm generations:

```
echidna-parade justlen.sol --config config.yaml --contract TEST --timeout 120 --gen_time 30 --ncores 8 --always turn_on_length_checking push_1 plus5 test_long_64 test_long_128
Starting echidna-parade with config=Config(files=['/Users/adg326/echidna-parade/examples/justlen.sol'], name='parade.82538', contract='TEST', config=<_io.TextIOWrapper name='config.yaml' mode='r' encoding='UTF-8'>, ncores=8, corpus_dir=None, timeout=120, gen_time=30, seed=None, minseqLen=10, maxseqLen=300, prob=0.5, always=['turn_on_length_checking', 'push_1', 'plus5', 'test_long_64', 'test_long_128'])

Results will be written to: /Users/adg326/echidna-parade/examples/parade.82538
Identified 14 public functions: push_1, pop_1, double, plus5, halve, decimate, empty1, empty2, empty3, turn_on_length_checking, turn_off_length_checking, test_long_8, test_long_64, test_long_128

RUNNING INITIAL CORPUS GENERATION
- LAUNCHING echidna-test in parade.82538/initial blacklisting [  ] with seqLen 100
parade.82538/initial FAILED
NEW FAILURE: assertion in test_long_8: failed!💥  

SWARM GENERATION #1: ELAPSED TIME 38.62 SECONDS / 120
- LAUNCHING echidna-test in parade.82538/gen.1.0 blacklisting [ halve, decimate, empty3 ] with seqLen 100
- LAUNCHING echidna-test in parade.82538/gen.1.1 blacklisting [ pop_1, halve, decimate, empty2, empty3, test_long_8 ] with seqLen 100
- LAUNCHING echidna-test in parade.82538/gen.1.2 blacklisting [ pop_1, double, halve, decimate, empty1, empty2, empty3 ] with seqLen 239
- LAUNCHING echidna-test in parade.82538/gen.1.3 blacklisting [ empty1, empty2, empty3, test_long_8 ] with seqLen 296
- LAUNCHING echidna-test in parade.82538/gen.1.4 blacklisting [ double ] with seqLen 100
- LAUNCHING echidna-test in parade.82538/gen.1.5 blacklisting [ empty1, turn_off_length_checking, test_long_8 ] with seqLen 208
- LAUNCHING echidna-test in parade.82538/gen.1.6 blacklisting [ pop_1, decimate, empty2 ] with seqLen 100
- LAUNCHING echidna-test in parade.82538/gen.1.7 blacklisting [ pop_1, double, halve, turn_off_length_checking, test_long_8 ] with seqLen 86
parade.82538/gen.1.2 FAILED
NEW FAILURE: assertion in test_long_64: failed!💥  
NEW FAILURE: assertion in test_long_128: failed!💥  
parade.82538/gen.1.0 FAILED
parade.82538/gen.1.1 FAILED
parade.82538/gen.1.4 FAILED
parade.82538/gen.1.6 FAILED

SWARM GENERATION #2: ELAPSED TIME 86.73 SECONDS / 120
- LAUNCHING echidna-test in parade.82538/gen.2.0 blacklisting [ decimate, empty1, empty2, empty3 ] with seqLen 19
- LAUNCHING echidna-test in parade.82538/gen.2.1 blacklisting [ pop_1, empty1, empty3, turn_off_length_checking, test_long_8 ] with seqLen 103
- LAUNCHING echidna-test in parade.82538/gen.2.2 blacklisting [ halve, empty1, empty2, empty3, test_long_8 ] with seqLen 226
- LAUNCHING echidna-test in parade.82538/gen.2.3 blacklisting [ halve, decimate, empty1, empty3 ] with seqLen 100
- LAUNCHING echidna-test in parade.82538/gen.2.4 blacklisting [ pop_1, double, decimate, empty2, test_long_8 ] with seqLen 100
- LAUNCHING echidna-test in parade.82538/gen.2.5 blacklisting [ double, empty1, turn_off_length_checking, test_long_8 ] with seqLen 20
- LAUNCHING echidna-test in parade.82538/gen.2.6 blacklisting [ pop_1, halve, empty2, turn_off_length_checking, test_long_8 ] with seqLen 194
- LAUNCHING echidna-test in parade.82538/gen.2.7 blacklisting [ halve, decimate, empty1, empty2, empty3, turn_off_length_checking ] with seqLen 100
parade.82538/gen.2.4 FAILED
parade.82538/gen.2.3 FAILED
parade.82538/gen.2.7 FAILED
parade.82538/gen.2.0 FAILED
parade.82538/gen.2.1 FAILED
parade.82538/gen.2.5 FAILED
parade.82538/gen.2.2 FAILED
parade.82538/gen.2.6 FAILED
DONE!

SOME TESTS FAILED

Property results:
========================================
assertion in test_long_8: failed!💥  
FAILED 8 TIMES
See: parade.82538/initial/echidna.out, parade.82538/gen.1.2/echidna.out, parade.82538/gen.1.0/echidna.out, parade.82538/gen.1.4/echidna.out, parade.82538/gen.1.6/echidna.out, parade.82538/gen.2.3/echidna.out, parade.82538/gen.2.7/echidna.out, parade.82538/gen.2.0/echidna.out
========================================
assertion in test_long_64: failed!💥  
FAILED 9 TIMES
See: parade.82538/gen.1.2/echidna.out, parade.82538/gen.2.4/echidna.out, parade.82538/gen.2.3/echidna.out, parade.82538/gen.2.7/echidna.out, parade.82538/gen.2.0/echidna.out, parade.82538/gen.2.1/echidna.out, parade.82538/gen.2.5/echidna.out, parade.82538/gen.2.2/echidna.out, parade.82538/gen.2.6/echidna.out
========================================
assertion in test_long_128: failed!💥  
FAILED 11 TIMES
See: parade.82538/gen.1.2/echidna.out, parade.82538/gen.1.0/echidna.out, parade.82538/gen.1.1/echidna.out, parade.82538/gen.2.4/echidna.out, parade.82538/gen.2.3/echidna.out, parade.82538/gen.2.7/echidna.out, parade.82538/gen.2.0/echidna.out, parade.82538/gen.2.1/echidna.out, parade.82538/gen.2.5/echidna.out, parade.82538/gen.2.2/echidna.out, parade.82538/gen.2.6/echidna.out
```
