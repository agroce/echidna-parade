*****

The echidna-parade tool has been officially "adopted" by Trail of Bits.  The official repo and current verion is at:

https://github.com/crytic/echidna-parade

Thanks!

*****


This is an experimental script that uses configuration variance and a common corpus to try to throughly test a smart contract (or multiple contracts) with the Echidna smart-contract fuzzer (https://github.com/crytic/echidna).

It runs Echidna instances in parallel, and uses two basic ideas derived from my research:

- swarm testing (https://agroce.github.io/issta12.pdf)

- test length matters (https://agroce.github.io/ase08.pdf)

In particular, after an initial run to generate low-hanging-fruit easy pickings in terms of coverage, future runs will consist of a number of parallel runs (determined by an --ncores argument or however many cores Python thinks you have) where each run randomly omits some functions (if you have a list already, it's respected and added to), and the sequence length and search strategy are also varied.

Usage is almost like Echidna; in fact if you just use the same arguments as to Echidna, it'll probably work.  E.g.,

```
> echidna-parade contract.sol --config config.yaml --contract TEST
```

will likely do something reasonable.  By default "generations" of testing are 5 minutes in length, and the testing runs for an hour.

Our [ISSTA tool paper](https://agroce.github.io/issta21.pdf) explains more about the rationale and effectiveness of echidna-parade.

-----------

Try out the example in the 'examples' directory.  Compare:

```
> echidna-test justlen.sol --config config.yaml --contract TEST
```

vs. what you can get with some knowledge of which functions not to omit from tests, and the same 120 seconds of testing with fast swarm generations:

```
> echidna-parade justlen.sol --config config.yaml --contract TEST --timeout 120 --initial_time 30 --gen_time 30 --ncores 8 --always "TEST.turn_on_length_checking()" "TEST.push_1()" "TEST.plus5()" "TEST.test_long_64()" "TEST.test_long_128()"
```

