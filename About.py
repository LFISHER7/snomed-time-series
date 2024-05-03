import streamlit as st

st.set_page_config(
    page_title="About",
    page_icon="❓",
)

st.markdown(
    """
    ## SNOMED CT Explorer 🔍

    Visualise recording of SNOMED CT codes in primary care in England using [data provided by NHS Digital](https://digital.nhs.uk/data-and-information/publications/statistical/mi-snomed-code-usage-in-primary-care).

    ### What is SNOMED CT?

    SNOMED CT is a [clinical terminology system](https://www.bennett.ox.ac.uk/blog/2023/06/an-introduction-to-clinical-codes-and-terminology-systems/) which is mandated for capturing clinical terms within electronic
    patient records for all NHS providers in England. For example, describing a patient's medical history or recording a medical procedure.
    
    There are three components to SNOMED CT:

    * **Concepts** - clinical thoughts represented by a unique numeric code.
    * **Descriptions** - human readable terms associated with concepts.
    * **Relationships** - links between concepts. These links form a hierarchies whereby concepts are organised from the general to the more detailed.

    ### What data is available?

    Each year, NHS Digital releases a dataset containing the total number of times each SNOMED CT concept code is added to GP patient records in England throughout the year. This data is available from 2011.

    The data contains the following information for each code:

    * `SNOMED_Concept_ID` - Numeric codes representing SNOMED concepts which have been added to a patient record in a general practice system during the reporting period.
    * `Description` - Description associated with the SNOMED_Concept_ID. 
    * `Usage` - The number of times that the SNOMED_Concept_ID was added into any patient record within the reporting period.
    * `Active_at_Start` - Whether the SNOMED_Concept_ID is active on the first day of the reporting period.
    * `Active_at_End` - Whether the SNOMED_Concept_ID is active on the last day of the reporting period. 

    #### Useful to know

    * Patients may have multiple codes added at different times throughout the year, so the counts presented do not represent the number of patients. You can't use this data to estimate disease prevalence.
    * Code usage is rounded to the nearest 10. Codes with counts <5 are not shown.
    * Years run between  1 Aug and 31 July.
    * Data prior to 2019 was predominantly submitted in READ2 or CTV3. These have been mapped forward to corresponding SNOMED CT codes.

    ### How does it work?

    This explorer has 3 options for exploring this data:

    1. **Entering a single code** - Explore usage over time for a single code.
    2. **Uploading a codelist** - Explore usage over time for a list of codes in a local [codelist](https://www.bennett.ox.ac.uk/blog/2023/09/what-are-codelists-and-how-are-they-constructed/).
    3. **Finding a codelist on OpenCodelists** - Explore usage over time for a list of codes on [OpenCodelists](https://opencodelists.org/).

    """
)
