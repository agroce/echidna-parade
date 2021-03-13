from __future__ import print_function

import argparse
from collections import namedtuple
import glob
import multiprocessing
import os
import random
import shutil
from slither import Slither
import subprocess
import sys
import time
import yaml


def generate_config(rng, public, basic, bases, config, prefix=None, initial=False):
    new_config = dict(basic)
    new_config["filterFunctions"] = []
    new_config["filterBlacklist"] = True
    if initial:
        new_config["timeout"] = config.initial_time
    basic_list = []
    blacklist = True
    if "filterFunctions" in basic:
        basic_list = basic["filterFunctions"]
        if "filterBlacklist" in basic:
            if not basic["filterBlacklist"]:
                blacklist = False
    excluded = []
    for f in public:
        if blacklist:
            if f in config.always:
                continue
            if f in basic_list:
                excluded.append(f)
            elif (not initial) and (rng.random() > config.prob):
                excluded.append(f)
        else:
            if f in config.always:
                continue
            if f in basic_list:
                if (not initial) and (rng.random() <= config.prob):
                    excluded.append(f)
            else:
                excluded.append(f)
    if (len(excluded) == len(public)) and (len(public) > 0):
        # This should be quite rare unless you have very few functions or a very low config.prob!
        print("Degenerate blacklist configuration, trying again...")
        return generate_config(rng, public, basic, bases, config, prefix, initial)
    new_config["filterFunctions"] = excluded
    if not initial:
        new_config["corpusDir"] = "corpus"
        new_config["mutConsts"] = []
        for i in range(4):
            # The below is pretty ad-hoc, you can uses bases to over-ride
            new_config["mutConsts"].append(random.choice([0, 1, 2, 3, 1000, 2000]))
        if rng.random() < config.PdefaultLen:
            new_config["seqLen"] = random.randrange(config.minseqLen, config.maxseqLen)
        if rng.random() < config.PdefaultDict:
            new_config["dictFreq"] = random.randrange(5, 95) / 100.0
        if bases:
            base = rng.choose(bases)
            for k in base:
                new_config[k] = base[k]

    return new_config


def make_echidna_process(prefix, rng, public_functions, base_config, bases, config, initial=False):
    g = generate_config(rng, public_functions, base_config, bases, config, prefix=prefix,
                        initial=initial)
    print("- LAUNCHING echidna-test in", prefix, "blacklisting [", ", ".join(g["filterFunctions"]),
          "] with seqLen", g["seqLen"], "dictFreq", g["dictFreq"], "and mutConsts ", g.setdefault("mutConsts", [1, 1, 1, 1]))
    os.mkdir(prefix)
    if not initial:
        os.mkdir(prefix + "/corpus")
        os.mkdir(prefix + "/corpus/coverage")
        for f in glob.glob(base_config["corpusDir"] + "/coverage/*.txt"):
            shutil.copy(f, prefix + "/corpus/coverage/")
    with open(prefix + "/config.yaml", 'w') as yf:
        yf.write(yaml.dump(g))
        outf = open(prefix + "/echidna.out", 'w')
        call = ["echidna-test"]
    call.extend(config.files)
    call.extend(["--config", "config.yaml"])
    if config.contract is not None:
        call.extend(["--contract", config.contract])
        call.extend(["--format", "text"])
    return (prefix, subprocess.Popen(call, stdout=outf, stderr=outf, cwd=os.path.abspath(prefix)), outf)


def process_failures(failed_props, prefix):
    with open(prefix + "/echidna.out", 'r') as ffile:
        for line in ffile:
            if "failed" in line[:-1]:
                if line[:-1] not in failed_props:
                    print("NEW FAILURE:", line[:-1])
                    failed_props[line[:-1]] = [prefix]
                else:
                    failed_props[line[:-1]].append(prefix)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=os.path.abspath, nargs='+', default=None,
                        help='FILES argument for echidna-test')
    parser.add_argument('--name', type=str, default="parade." + str(os.getpid()),
                        help='name for parade (directory where output files are placed)')
    parser.add_argument('--resume', type=str, default=None,
                        help='parade to resume (directory name with existing run)')
    parser.add_argument('--contract', type=str, default=None,
                        help='CONTRACT argument for echidna-test')
    parser.add_argument('--config', type=argparse.FileType('r'), default=None,
                        help='CONFIG argument for echidna-test')
    parser.add_argument('--bases', type=argparse.FileType('r'), default=None,
                        help='file containing a list of additional configuration files to randomly choose among for non-initial runs')
    parser.add_argument('--ncores', type=int, default=multiprocessing.cpu_count(),
                        help='Number of cores to use (swarm instances to run in parallel (default = all available)')
    parser.add_argument('--corpus_dir', type=os.path.abspath, default=None,
                        help='Directory to store the echidna-parade corpus (useful when existing corpus available)')
    parser.add_argument('--timeout', type=int, default=3600,
                        help='Total testing time, use -1 for no timeout (default = 3600)')
    parser.add_argument('--gen_time', type=int, default=300,
                        help='Per-generation testing time (default = 300)')
    parser.add_argument('--initial_time', type=int, default=300,
                        help='Initial run testing time (default = 300)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed (default = None).')
    parser.add_argument('--minseqLen', type=int, default=10,
                        help='Minimum sequence length to use (default = 10).')
    parser.add_argument('--maxseqLen', type=int, default=300,
                        help='Maximum sequence length to use (default = 300).')
    parser.add_argument('--PdefaultLen', type=float, default=0.5,
                        help="Probability of using default/base length (default = 0.5)")
    parser.add_argument('--PdefaultDict', type=float, default=0.5,
                        help="Probability of using default/base dictionary usage frequency (default = 0.5)")
    parser.add_argument('--prob', type=float, default=0.5,
                        help='Probability of including functions in swarm config (default = 0.5).')
    parser.add_argument('--always', type=str, nargs='+', default=[],
                        help='functions to ALWAYS include in swarm configurations')
    parsed_args = parser.parse_args(sys.argv[1:])
    return (parsed_args, parser)


def make_config(pargs, parser):
    """
    Process the raw arguments, returning a namedtuple object holding the
    entire configuration, if everything parses correctly.
    """
    pdict = pargs.__dict__
    if pargs.files is None:
        parser.print_help()
        raise ValueError('You must specify some files to test!')
    # create a namedtuple object for fast attribute lookup
    key_list = list(pdict.keys())
    arg_list = [pdict[k] for k in key_list]
    Config = namedtuple('Config', key_list)
    nt_config = Config(*arg_list)
    return nt_config


def main():
    parsed_args, parser = parse_args()
    config = make_config(parsed_args, parser)
    print("Starting echidna-parade with config={}".format(config))

    if config.resume is None:
        if os.path.exists(config.name):
            raise ValueError(config.name + ": refusing to overwrite existing directory; perhaps you meant to --resume?")
        else:
            os.mkdir(config.name)

        print()
        print("Results will be written to:", os.path.abspath(config.name))
    else:
        print("Attempting to resume testing from", config.resume)
        if not os.path.exists(config.resume):
            raise ValueError("No parade directory found!")
        if not (os.path.exists(config.resume + "/initial")):
            raise ValueError("No initial run present, does not look like a parade directory!")

    rng = random.Random(config.seed)

    base_config = {}
    y = yaml.safe_load(config.config)
    for key in y:
        if key not in ["timeout", "testLimit", "stopOnFail", "corpusDir", "coverage"]:
            base_config[key] = y[key]
    base_config["timeout"] = config.gen_time
    if "seqLen" not in base_config:
        base_config["seqLen"] = min(max(config.minseqLen, 100), config.maxseqLen)
    if "dictFreq" not in base_config:
        base_config["dictFreq"] = 0.40
    if config.corpus_dir is not None:
        base_config["corpusDir"] = config.corpus_dir
    else:
        if config.resume is None:
            base_config["corpusDir"] = os.path.abspath(config.name + "/corpus")
        else:
            base_config["corpusDir"] = os.path.abspath(config.resume + "/corpus")
    base_config["stopOnFail"] = False
    base_config["coverage"] = True
    if not os.path.exists(base_config["corpusDir"]):
        os.mkdir(base_config["corpusDir"])
	
    bases = []
    if config.bases is not None:
        with open(config.bases, 'r') as bfile:
            for line in bfile:
                base = line[:-1]
                y = yaml.safe_load(base)
                bases.append(y)

    prop_prefix = "echidna_"
    if "prefix" in base_config:
        prop_prefix = base_config["prefix"]

    public_functions = []
    for f in config.files:
        if not os.path.exists(f):
            raise ValueError('Specified file ' + f + ' does not exist!')
        slither = Slither(f)
        for contract in slither.contracts:
            for function in contract.functions_entry_points:
                if not function.is_implemented:
                    continue
                fname = function.full_name
                if function.is_constructor or (fname.find(prop_prefix) == 0):
                    # Don't bother blacklisting constructors or echidna properties
                    continue
                if function.visibility in ["public", "external"]:
                    public_functions.append(contract.name + "." + fname)

    print("Identified", len(public_functions), "public and external functions:", ", ".join(public_functions))
    if len(public_functions) == 0:
        print("WARNING: something may be wrong; no public or external functions were found!")
        print()

    failures = []
    failed_props = {}
    start = time.time()
    elapsed = time.time() - start

    if config.resume is None:
        print()
        print("RUNNING INITIAL CORPUS GENERATION")
        prefix = config.name + "/initial"
        (pname, p, outf) = make_echidna_process(prefix, rng, public_functions, base_config, bases, config, initial=True)
        p.wait()
        outf.close()
        if p.returncode != 0:
            print(pname, "FAILED")
            process_failures(failed_props, pname)
            failures.append(pname + "/echidna.out")

    generation = 1
    if config.resume is None:
        run_name = config.name
    else:
        run_name = config.resume
        generation = 1
        while os.path.exists(run_name + "/gen." + str(generation) + ".0"):
            generation += 1
        print("RESUMING PARADE AT GENERATION", generation)

    elapsed = time.time() - start
    while (config.timeout == -1) or (elapsed < config.timeout):
        print()
        print("SWARM GENERATION #" + str(generation) + ": ELAPSED TIME", round(elapsed, 2), "SECONDS",
              ("/ " + str(config.timeout)) if config.timeout != -1 else "")
        ps = []
        for i in range(config.ncores):
            prefix = run_name + "/gen." + str(generation) + "." + str(i)
            ps.append(make_echidna_process(prefix, rng, public_functions, base_config, bases, config))
        any_not_done = True
        gen_start = time.time()
        while any_not_done:
            any_not_done = False
            done = []
            for (pname, p, outf) in ps:
                if p.poll() is None:
                    any_not_done = True
                else:
                    done.append((pname, p, outf))
                    outf.close()
                    for f in glob.glob(pname + "/corpus/coverage/*.txt"):
                        if not os.path.exists(base_config["corpusDir"] + "/coverage/" + os.path.basename(f)):
                            print("COLLECTING NEW COVERAGE:", f)
                            shutil.copy(f, base_config["corpusDir"] + "/coverage")
                    if p.returncode != 0:
                        print(pname, "FAILED")
                        process_failures(failed_props, pname)
                        failures.append(pname + "/echidna.out")
            for d in done:
                ps.remove(d)
            gen_elapsed = time.time() - gen_start
            if gen_elapsed > (config.gen_time + 30):  # full 30 second fudge factor here!
                print("Generation still running after timeout!")
                for (pname, p, outf) in ps:
                    outf.close()
                    for f in glob.glob(pname + "/corpus/coverage/*.txt"):
                        if not os.path.exists(base_config["corpusDir"] + "/coverage/" + os.path.basename(f)):
                            print("COLLECTING NEW COVERAGE:", f)
                            shutil.copy(f, base_config["corpusDir"] + "/coverage")
                    if p.poll() is None:
                        p.kill()
                any_not_done = False
        elapsed = time.time() - start
        generation += 1
    print("DONE!")
    print()
    if len(failures) == 0:
        print("NO FAILURES")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED")
        print()
        print("Property results:")
        for prop in sorted(failed_props.keys(), key=lambda x: len(failed_props[x])):
            print("="*40)
            print(prop)
            print("FAILED", len(failed_props[prop]), "TIMES")
            print("See:", ", ".join(map(lambda p: p+"/echidna.out", failed_props[prop])))

        sys.exit(len(failures))


if __name__ == '__main__':
    main()
