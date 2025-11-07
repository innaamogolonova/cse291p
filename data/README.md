# Data layout

This project does not commit ARVO datasets directly.  
Run `./scripts/prep_data.sh` to fetch:

- data/arvo/arvo.db (from ARVO-Meta Releases)
- data/arvo/ARVO-Meta/
- data/arvo/memory_cases_asan.csv

To extract source code from a case run `bash scripts/extract_case.sh <case_number>`. Case numbers are `localID` in `memory_cases_asan.csv`.
Cases used for basic implementation:
289, 344, 362, 367, 25402

In the above, buggy source code is contained in directories that are not fuzzers (directories that doen't have some version of "fuzz" or "afl" in their names)
