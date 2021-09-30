# *******************************************************************************
# IBM Confidential                                                            *
#                                                                             *
# OCO Source Materials                                                        *
#                                                                             *
# (C) Copyright IBM Corp. 2021                                                *
#                                                                             *
# The source code for this program is not published or otherwise              *
# divested of its trade secrets, irrespective of what has been                *
# deposited with the U.S. Copyright Office.                                   *
# ******************************************************************************/

"""Utilities for building FHIR objects specific to ACD derived insights"""

from typing import List
from typing import Optional

from fhir.resources.attachment import Attachment
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.extension import Extension
from ibm_whcs_sdk.annotator_for_clinical_data.annotator_for_clinical_data_v1 import (
    InsightModelData,
)

from text_analytics import fhir_object_utils
from text_analytics import insight_constants
from text_analytics.fhir_object_utils import create_coding
from text_analytics.fhir_object_utils import create_confidence_extension


# Creates extension to hold the NLP output (ACD results).
def create_ACD_output_extension(acd_output):
    # TODO: save to an external MinIO location.  For now, just put in a dummy String
    insight_detail_ext = Extension.construct()
    insight_detail_ext.url = insight_constants.INSIGHT_ACD_OUTPUT_URL
    attachment = Attachment.construct()
    attachment.url = "uri://path/acd-123.json"
    insight_detail_ext.valueAttachment = attachment
    return insight_detail_ext


# ACD will often return multiple codes from one system in a comma delimited list.
# To be used for resources being augemented with insights - adds extension indicating the code is derived.
# Split the list, then create a separate coding system entry for each one with a derived extension.
def _append_coding_entries_with_extension(codeable_concept, code_url, code_ids):
    for code_id in code_ids.split(","):
        # code_entry = _find_codable_concept(codeable_concept, id, code_url)
        fhir_object_utils.append_derived_by_nlp_coding(
            codeable_concept, system=code_url, code=code_id
        )


# ACD will often return multiple codes from one system in a comma delimited list.
# To be used for resources created from insights - does not add an extension indicating the code is derived.
# Split the list, then create a separate coding system entry for each one (no derived extension).
def _append_coding_entries(codeable_concept, code_url, code_ids):
    for code_id in code_ids.split(","):
        fhir_object_utils.append_coding(codeable_concept, code_url, code_id)


def _count_codes(codeable_concept: CodeableConcept) -> int:
    return len(codeable_concept.coding) if codeable_concept.coding else 0


# Adds codes from the concept to the codeable_concept.
# To be used for resources being augemented with insights - adds extension indicating the code is derived.
# Parameters:
#   concept - ACD concept
#   codeable_concept - FHIR codeable concept the codes will be added to
def append_codings_with_nlp_derived_extension(acd_concept, codeable_concept) -> int:
    num_codes_before: int = _count_codes(codeable_concept)

    if acd_concept.cui is not None:
        # For CUIs, we do not handle comma-delimited values (have not seen that we ever have more than one value)
        # We use the preferred name from UMLS for the display text
        fhir_object_utils.append_derived_by_nlp_coding(
            codeable_concept,
            insight_constants.UMLS_URL,
            acd_concept.cui,
            acd_concept.preferred_name,
        )

    if acd_concept.snomed_concept_id is not None:
        _append_coding_entries_with_extension(
            codeable_concept,
            insight_constants.SNOMED_URL,
            acd_concept.snomed_concept_id,
        )
    if acd_concept.nci_code is not None:
        _append_coding_entries_with_extension(
            codeable_concept, insight_constants.NCI_URL, acd_concept.nci_code
        )
    if acd_concept.loinc_id is not None:
        _append_coding_entries_with_extension(
            codeable_concept, insight_constants.LOINC_URL, acd_concept.loinc_id
        )
    if acd_concept.mesh_id is not None:
        _append_coding_entries_with_extension(
            codeable_concept, insight_constants.MESH_URL, acd_concept.mesh_id
        )
    if acd_concept.icd9_code is not None:
        _append_coding_entries_with_extension(
            codeable_concept, insight_constants.ICD9_URL, acd_concept.icd9_code
        )
    if acd_concept.icd10_code is not None:
        _append_coding_entries_with_extension(
            codeable_concept, insight_constants.ICD10_URL, acd_concept.icd10_code
        )
    if acd_concept.rx_norm_id is not None:
        _append_coding_entries_with_extension(
            codeable_concept, insight_constants.RXNORM_URL, acd_concept.rx_norm_id
        )

    return _count_codes(codeable_concept) - num_codes_before


# Adds codes from the concept to the codeable_concept.
# To be used for resources created from insights - does not add an extension indicating the code is derived.
# Parameters:
#   concept - ACD concept
#   codeable_concept - FHIR codeable concept the codes will be added to
def add_codings(concept, codeable_concept):
    if concept.cui is not None:
        # For CUIs, we do not handle comma-delimited values (have not seen that we ever have more than one value)
        # We use the preferred name from UMLS for the display text
        code_entry = _find_codable_concept(
            codeable_concept, concept.cui, insight_constants.UMLS_URL
        )
        if code_entry is None:
            coding = create_coding(insight_constants.UMLS_URL, concept.cui)
            coding.display = concept.preferred_name
            codeable_concept.coding.append(coding)
    if concept.snomed_concept_id is not None:
        _append_coding_entries(
            codeable_concept, insight_constants.SNOMED_URL, concept.snomed_concept_id
        )
    if concept.nci_code is not None:
        _append_coding_entries(
            codeable_concept, insight_constants.NCI_URL, concept.nci_code
        )
    if concept.loinc_id is not None:
        _append_coding_entries(
            codeable_concept, insight_constants.LOINC_URL, concept.loinc_id
        )
    if concept.mesh_id is not None:
        _append_coding_entries(
            codeable_concept, insight_constants.MESH_URL, concept.mesh_id
        )
    if concept.icd9_code is not None:
        _append_coding_entries(
            codeable_concept, insight_constants.ICD9_URL, concept.icd9_code
        )
    if concept.icd10_code is not None:
        _append_coding_entries(
            codeable_concept, insight_constants.ICD10_URL, concept.icd10_code
        )
    if concept.rx_norm_id is not None:
        _append_coding_entries(
            codeable_concept, insight_constants.RXNORM_URL, concept.rx_norm_id
        )


# Adds codes from the drug concept to the codeable_concept.
# To be used for resources created from insights - does not add an extension indicating the code is derived.
# Parameters:
#   acd_drug - ACD concept for the drug
#   codeable_concept - FHIR codeable concept the codes will be added to
def add_codings_drug(acd_drug, codeable_concept):
    if acd_drug.get("cui") is not None:
        # For CUIs, we do not handle comma-delimited values (have not seen that we ever have more than one value)
        # We use the preferred name from UMLS for the display text
        code_entry = _find_codable_concept(
            codeable_concept, acd_drug.get("cui"), insight_constants.UMLS_URL
        )
        if code_entry is None:
            coding = create_coding(insight_constants.UMLS_URL, acd_drug.get("cui"))
            coding.display = acd_drug.get("drugSurfaceForm")
            codeable_concept.coding.append(coding)
    if acd_drug.get("rxNormID") is not None:
        _append_coding_entries(
            codeable_concept, insight_constants.RXNORM_URL, acd_drug.get("rxNormID")
        )


# Looks through the array of the codeable_concept for an entry matching the id and system.
# Returns the entry if found, or None if not found.
def _find_codable_concept(codeable_concept, id, system):
    for entry in codeable_concept.coding:
        if entry.system == system and entry.code == id:
            return entry
    return None


def get_diagnosis_confidences(
    insight_model_data: InsightModelData,
) -> Optional[List[Extension]]:
    confidence_list = []

    try:
        confidence_list.append(
            create_confidence_extension(
                insight_constants.CONFIDENCE_SCORE_EXPLICIT,
                insight_model_data.diagnosis.usage.explicit_score,
            )
        )
    except AttributeError:
        pass

    try:
        confidence_list.append(
            create_confidence_extension(
                insight_constants.CONFIDENCE_SCORE_PATIENT_REPORTED,
                insight_model_data.diagnosis.usage.patient_reported_score,
            )
        )
    except AttributeError:
        pass

    try:
        confidence_list.append(
            create_confidence_extension(
                insight_constants.CONFIDENCE_SCORE_DISCUSSED,
                insight_model_data.diagnosis.usage.discussed_score,
            )
        )
    except AttributeError:
        pass

    try:
        confidence_list.append(
            create_confidence_extension(
                insight_constants.CONFIDENCE_SCORE_FAMILY_HISTORY,
                insight_model_data.diagnosis.family_history_score,
            )
        )
    except AttributeError:
        pass

    try:
        confidence_list.append(
            create_confidence_extension(
                insight_constants.CONFIDENCE_SCORE_SUSPECTED,
                insight_model_data.diagnosis.suspected_score,
            )
        )
    except AttributeError:
        pass

    return confidence_list if confidence_list else None


def get_medication_confidences(
    insight_model_data: InsightModelData,
) -> Optional[List[Extension]]:
    """Returns a list of confidence extensions

    The list is suitable to be added to the insight span extensions array.
     Args:
        insight_model_data - model data for the insight

     Returns:
        collection of confidence extensions, or None if no confidence info was available
    """
    # Medication has 5 types of confidence scores
    # For alpha only pulling medication.usage scores
    # Not using startedEvent scores, stoppedEvent scores, doseChangedEvent scores, adversetEvent scores
    # Per documentation in InsightModelData, most structural components of the scores is optional,
    # Handling that with exception handlers, since we expect those to be there based on experience
    confidence_list = []

    try:
        confidence_list.append(
            create_confidence_extension(
                insight_constants.CONFIDENCE_SCORE_MEDICATION_TAKEN,
                insight_model_data.medication.usage.taken_score,
            )
        )
    except AttributeError:
        pass

    try:
        confidence_list.append(
            create_confidence_extension(
                insight_constants.CONFIDENCE_SCORE_MEDICATION_CONSIDERING,
                insight_model_data.medication.usage.considering_score,
            )
        )
    except AttributeError:
        pass

    try:
        confidence_list.append(
            create_confidence_extension(
                insight_constants.CONFIDENCE_SCORE_MEDICATION_DISCUSSED,
                insight_model_data.medication.usage.discussed_score,
            )
        )
    except AttributeError:
        pass

    try:
        confidence_list.append(
            create_confidence_extension(
                insight_constants.CONFIDENCE_SCORE_MEDICATION_MEASUREMENT,
                insight_model_data.medication.usage.lab_measurement_score,
            )
        )
    except AttributeError:
        pass

    return confidence_list if confidence_list else None
