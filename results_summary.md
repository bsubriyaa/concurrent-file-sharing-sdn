| Scenario | Metric | baseline | sdn | sdn_nolimit | sdn_limit |
|---|---|---|---|---|---|
| attack | answered_by_server | 99.00 ± 0.00 (n=1) | 3.00 ± 0.00 (n=1) | - | - |
| attack | attempts | 99.00 ± 0.00 (n=1) | 20.00 ± 0.00 (n=1) | - | - |
| concurrent3 | hash_ok | 1.00 ± 0.00 (n=9) | 1.00 ± 0.00 (n=9) | - | - |
| concurrent3 | mbps | 3.45 ± 1.04 (n=9) | 3.68 ± 1.98 (n=9) | - | - |
| concurrent3 | seconds | 13.16 ± 4.28 (n=9) | 13.17 ± 4.00 (n=9) | - | - |
| hog_hog | hash_ok | - | - | 1.00 ± 0.00 (n=36) | 1.00 ± 0.00 (n=24) |
| hog_hog | mbps | - | - | 1.92 ± 1.17 (n=36) | 1.68 ± 0.37 (n=24) |
| hog_hog | seconds | - | - | 25.61 ± 8.71 (n=36) | 25.97 ± 4.97 (n=24) |
| hog_victim | hash_ok | - | - | 1.00 ± 0.00 (n=7) | 1.00 ± 0.00 (n=6) |
| hog_victim | mbps | - | - | 1.72 ± 0.40 (n=7) | 3.47 ± 1.84 (n=6) |
| hog_victim | seconds | - | - | 25.72 ± 7.06 (n=7) | 14.15 ± 4.82 (n=6) |
| single | hash_ok | 1.00 ± 0.00 (n=10) | 1.00 ± 0.00 (n=10) | - | - |
| single | mbps | 9.16 ± 1.19 (n=10) | 9.64 ± 0.03 (n=10) | - | - |
| single | seconds | 4.68 ± 0.89 (n=10) | 4.35 ± 0.01 (n=10) | - | - |
| under_attack | hash_ok | 1.00 ± 0.00 (n=3) | 1.00 ± 0.00 (n=3) | - | - |
| under_attack | mbps | 9.58 ± 0.10 (n=3) | 9.61 ± 0.06 (n=3) | - | - |
| under_attack | seconds | 4.38 ± 0.05 (n=3) | 4.36 ± 0.03 (n=3) | - | - |

Jain fairness index (1.0 = perfectly fair):

| Scenario | baseline | sdn | sdn_nolimit | sdn_limit |
|---|---|---|---|---|
| concurrent3 | 0.999 (3 clients) | 0.943 (3 clients) | - | - |
