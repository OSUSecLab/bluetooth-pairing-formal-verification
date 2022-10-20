Overview
-------
This repository contains [Tamarin](https://tamarin-prover.github.io/), a protocol security  verification tool, models for Bluetooth secure pairing protocols:  
Passkey Entry (PE) and Numeric comparison (NC). These models are part of security research paper: *Extrapolating Formal Analysis to Uncover Attacks in Bluetooth Passkey Entry Pairing* accepted in Network and Distributed System Security (NDSS) Symposium 2023. The paper contains further details of pairing protocols, model details and results.  Some of the model ideas are borrowed from [SGX-Enclave-Formal-Verification](https://github.com/OSUSecLab/SGX-Enclave-Formal-Verification).       


Directory and File Structure
-----------------------

├── patched
│   ├── gen_proof.py
│   ├── patched.spthy
│   └── run_times_of_lemmas.txt
└── vulnerable
    ├── a1-method-confusion-trace-annotated.pdf
    ├── a1-method-confusion-trace.pdf
    ├── a1.spthy
    ├── a2-reflection-trace-annotated.pdf
    ├── a2-reflection-trace.pdf
    ├── a2.spthy
    ├── a3.spthy
    ├── a3-static-passcode-trace-annotated.pdf
    ├── a3-static-passcode-trace.pdf
    ├── a4-group-guessing-trace-annotated.pdf
    ├── a4-group-guessing-trace.pdf
    ├── a4.spthy
    ├── a5-ghost-trace-annotated.pdf
    ├── a5-ghost-trace.pdf
    └── a5.spthy

2 directories, 19 files

2 directories, 17 files

The "vulnerable" folder contains all vulnerable Tamarin model files. The Tamarin model files are with extension *.spthy and corresponding attack trace files are in the form of PDF files. These trace files have suppressed action labels for generating short comprehensible traces. The user IDs in the annotated traces can be observed in the facts of form: MemA.. or MemB... which binds the pairing process rules. The original traces can be generated by running the provided commands in the individual code file. 


The "patched" folder contains the patched Tamarin model and a python script <gen_proof.py> to generate the proofs of all the lemmas. All model files contain further context information, code comments, and lemmas comments. For vulnerable model files, Tamarin heuristics and trace algorithm parameters are specified in the model files as comments.  


How to run the model files: 
---------------------------------
  Tamarin (v1.6.1) should be installed from GitHub repo https://github.com/tamarin-prover/tamarin-prover. python3 installation is also required to run the patched model file.  To generate the attack traces the run command is specified in the corresponding model file. To generate patched model proofs follow the steps below:
        1. open terminal in the patched folder. 
        2. Install python3 module
              python3 -m pip install prettytable 
        2. Run following command    
          

    python3 gen_proof.py --tam_code_file <patched_file_full_path>  --timeout_min 1440 --trace_algos SEQDFS

Here the `patched_file_full_path` should be a full path e.g., /home/user/dir/patched.spthy . The run time for the patched model is  approximately 1 day and 7 hours for all lemmas. Individual lemmas run times is provided in a separate file `run_times_of_lemmas.txt`.
