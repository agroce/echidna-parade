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
echidna-parade justlen.sol --config config.yaml --contract TEST --timeout 120 --gen_time 30 --ncores 8 --always "TEST.turn_on_length_checking()" "TEST.push_1()" "TEST.plus5()" "TEST.test_long_64()" "TEST.test_long_128()"
```

