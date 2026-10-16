# Data: the terms, quoted, and what they bind

Three public datasets of real people. The terms of each are quoted here before the first fetch,
and the loaders read the register below before they touch anything: a row that does not say
`Yes` with a date stops the loader (`facsimile/data/terms.py`). Nothing raw is committed;
`facsimile/data/checksums.json` records each file's SHA-256 at its first fetch and every later
read verifies it.

One rule sits on top of all three sets' terms, recorded because the Census terms state it:
**attacks stay inside the dataset.** Singling out, linkability and inference are measured
against the dataset's own control set and stop there. No outside data is ever joined to a
record, and nothing is ever done to put a name to one.

## Terms register

| Key | Dataset | Terms | Read | Permitted |
|---|---|---|---|---|
| `acs` | ACS PUMS, California 2018, one-year person file | Census Bureau terms below; folktables MIT | 2026-10-16 | Yes: analysis of public-use microdata with no attempt to identify anyone |
| `ieeecis` | IEEE-CIS Fraud Detection | Kaggle competition rules 7.A, 7.B, 8.B, read and recorded by project 09 | 2026-09-12 (09), reused 2026-10-16 | Yes: non-commercial use, results publishable, data and row-level derivatives not |
| `sparcs` | NY SPARCS de-identified inpatient discharges, 2024 | NYSDOH Data Use Policy Statement (revised February 2013) | 2026-10-16 | Yes: no controls on end use; attribution, access date and the disclaimer required |

## ACS PUMS via folktables

The American Community Survey public-use microdata sample, California, 2018, one-year person
file (`csv_pca.zip`), fetched from `www2.census.gov`. The task definitions (ACSIncome,
ACSEmployment) are from folktables 0.0.12, MIT licence.

The Census Bureau's terms, from its Data API terms of service
(https://www.census.gov/data/developers/about/terms-of-service.html, read 2026-10-16). The file is
fetched from the Bureau's file server rather than through the API, and these are the Bureau's
published terms for its data; they are quoted because they are the strictest statement it makes:

> Title 13 [...] requires the Census Bureau to publish data in a manner that does not permit use
> of the data alone, or in combination with other available information, to identify any
> particular respondent to a Census Bureau survey.

> The identification of a person or establishment or disclosure of information collected from
> that person or establishment in the course of a Census Bureau survey violates the assurances
> of confidentiality provided by federal law.

> Therefore, users will not use these data, alone or in combination with any other Census or
> non-Census data, to identify any individual person, household, business or other entity;
> not link or combine these data with information in any other Census or non-Census dataset in
> a manner that identifies an individual person, household, business or other entity;
> not publish information from these data files, particularly in combination with any other
> Census or non-Census data, in a manner that identifies any individual person, household,
> business or other entity;

> You may not use the Census Bureau name, or the like to imply endorsement of any product,
> service, or entity, not-for-profit, commercial or otherwise.

What they bind, and how this project honours them by construction:

- **No identification, no linking to outside data.** The attacks measure whether a row of the
  public-use file can be isolated, linked or inferred from a synthetic table, against the file's
  own control records, which is the risk the law names. No outside data is joined and no record
  is matched to a person. The attack target set is a set of row positions in the Bureau's own
  public file.
- **No endorsement.** Nothing here says or implies that the Census Bureau endorses it.

## IEEE-CIS Fraud Detection

Published by Vesta Corporation for the IEEE Computational Intelligence Society's 2019 challenge,
https://www.kaggle.com/competitions/ieee-fraud-detection. **The rules were read and recorded by
project 09 on 2026-09-12** (`docs/data.md` in the realtime-risk-platform repository) and are
reused here unchanged. The clauses that decide this project's use:

> **7.A Data Access and Use.** "You may access and use the Competition Data for non-commercial
> purposes only, including for participating in the Competition and on Kaggle.com forums, and
> for academic research and education."

> **7.B Data Security.** "You agree not to transmit, duplicate, publish, redistribute or
> otherwise provide or make available the Competition Data to any party not participating in
> the Competition." It also requires "reasonable and suitable measures to prevent persons who
> have not formally agreed to these Rules from gaining access to the Competition Data."

> **8.B Public Code Sharing.** "You are permitted to publicly share Competition Code, provided
> that such public sharing does not violate the intellectual property rights of any third party.
> [...] By so sharing, you are deemed to have licensed the shared code under an Open Source
> Initiative-approved license [...] that in no event limits commercial use."

What they bind here, as they bound 09:

- **Non-commercial.** This repository sells nothing and offers no service. The MIT licence on
  the code satisfies 8.B and does not and cannot relicense the data.
- **The data and any row-level derivative stay local.** A synthetic table fitted to this data is
  row-level output derived from it, so the whole table grid stays under `data/` (gitignored),
  is never uploaded to CI and is never served by the explorer. Results computed from it (risks,
  utilities, intervals) are publishable, which 7.B does not restrict.
- **Split ids are not published** for this set: a list of TransactionIDs is a row-level
  reference. The split manifest carries counts and SHA-256 hashes, and the split is exactly
  reproducible from the files and the seed. PLAN.md section 2.5 is amended to say so.
- **Nothing downloads the data.** The account holder downloads the archive; on the build
  desktop the loader reads the copy 09 verified, through `FACSIMILE_IEEE_CIS_DIR`, against 09's
  recorded checksums (copied into `facsimile/data/checksums.json`).

## NY SPARCS de-identified inpatient discharges

Hospital Inpatient Discharges (SPARCS De-Identified): 2024, dataset `sf4k-39ay` on Health Data NY
(https://health.data.ny.gov/d/sf4k-39ay), 2,196,737 discharges, published by the New York State
Department of Health. The public de-identified tier needs no application. The dataset's licence
field reads "See Terms of Use", and the Department's Data Use Policy Statement
(https://www.health.ny.gov/about/data_use.htm, revised February 2013, read 2026-10-16 at
`healthweb-back.health.ny.gov` because the main host's CDN refused this machine) is the text that
governs it. Quoted in full except its last two sentences, which concern the Department's own
legal position:

> The data accessed through this site does not include controls over its end use. However, as
> the data owner or authoritative source for the data, the Department of Health retains version
> control of datasets accessed. Once data has been downloaded, the Department makes no
> representation, warranty or guarantee of quality, nor does the Department vouch for any
> analyses conducted with data retrieved from this site.

> Unless otherwise noted on an individual document, file, web page or other item, the
> Department of Health grants users permission to reproduce materials published by the
> Department on this Website so long as the Department of Health is noted as the source, and
> the data the web page was accessed, along with the date of publication of the material cited,
> is noted. All copyright and other proprietary notices must be retained in the same form and
> manner as on the original and the contents may not be modified in any way. The user agrees to
> abide by all additional restrictions provided on this site as it may be updated from time to
> time.

> Finally, users must clearly state on any work product using the data that: "The New York
> State Department of Health makes no representation, warranty or guarantee relating to the
> data or analyses derived from these data."

The dataset page's own disclaimer, from its metadata (read 2026-10-16):

> The de-identified data file contains basic record level detail; it does not contain data that
> is protected health information (PHI) under the Health Insurance Portability and
> Accountability Act (HIPAA). The health information contained in the file is not individually
> identifiable; all data elements that are considered identifiable have been redacted.

What they bind here:

- **Attribution and the disclaimer** go in the README wherever a SPARCS number appears: source
  New York State Department of Health, Health Data NY dataset `sf4k-39ay`, accessed on the date
  in `checksums.json`, and the sentence above verbatim.
- **"The contents may not be modified"** governs reproducing the Department's materials. This
  project does not republish the file or any part of it: no row is committed, and the synthetic
  tables stay under `data/` like the raw file, so the question of a modified copy does not
  arise. That reading is the conservative one and is recorded so it can be checked.
- **The file is a de-identified public-use file**, and the attacks measure whether a row of it
  can be singled out, linked or inferred from a synthetic table against its own control set.
  Nothing is joined to it and no record is ever matched to a person.
- **The state revises the data** ("Data is subject to change"), so the fetch is in the portal's
  row order and its checksum is recorded; a revision is an error, not a moved number.

Read on 2026-10-16; the reading above confirmed by Peter the same day.

## Subsets

Each dataset is reduced to sixteen or seventeen attributes so the marginal methods are
tractable. The subset, the domain and the split of each are published under `results/<key>/`
(`datasheet.md`, `domain.json`, `split.json`) by `facsimile build`. Category sets come from the
test split and bin edges from the spec, so the domain spends no privacy budget on the people
the synthesisers are fitted on (`facsimile/prep.py` says why).
