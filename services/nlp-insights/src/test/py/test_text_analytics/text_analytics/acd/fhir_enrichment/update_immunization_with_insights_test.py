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

import json
import unittest

from deepdiff import DeepDiff
from fhir.resources.bundle import Bundle
from fhir.resources.immunization import Immunization
from ibm_whcs_sdk.annotator_for_clinical_data.annotator_for_clinical_data_v1 import (
    ContainerAnnotation,
)

from test_text_analytics.util.resources import UnitTestUsingExternalResource
from text_analytics.acd.fhir_enrichment.enrich_fhir_resource import (
    create_new_resources_from_insights,
    create_conditions_from_insights,
)
from text_analytics.acd.fhir_enrichment.enrich_fhir_resource import (
    enrich_resource_codeable_concepts,
)
from text_analytics.acd.fhir_enrichment.insights.update_codeable_concepts import (
    update_codeable_concepts_and_meta_with_insights,
    CodeableConceptAcdInsight,
)
from text_analytics.concept_text_adjustment import AdjustedConceptRef
from text_analytics.fields_of_interest import CodeableConceptRef, CodeableConceptRefType


class enhance_immunization_with_insights_test(UnitTestUsingExternalResource):
    def _check_results(
        self, immunization, acd_result, expected_immunization, full_output
    ):
        """
        This method assumes a single FHIR resource will be updated, and verifies that resource against the expected resource.
        Parmeters:
          immunization - FHIR Immunization input before insights are added
          acd_result - ACD ContainerAnnotation, used for mock ACD output
          expected_immunization - updated FHIR Immunization expected after insights added
          full_output (boolean) - if True, will output the full expected and actual results if they do not match
        """

        ai_results = [
            CodeableConceptAcdInsight(
                adjusted_concept=AdjustedConceptRef(
                    concept_ref=CodeableConceptRef(
                        type=CodeableConceptRefType.VACCINE,
                        code_ref=immunization.vaccineCode,
                        fhir_path="Immunization.vaccineCode",
                    ),
                    adjusted_text=immunization.vaccineCode.text,
                ),
                acd_response=acd_result,
            )
        ]

        num_updates = update_codeable_concepts_and_meta_with_insights(
            immunization, ai_results
        )

        differences = DeepDiff(
            expected_immunization, immunization, verbose_level=2
        ).pretty()
        if full_output:
            expected_str = "\n\nEXPECTED RESULTS:\n" + expected_immunization.json()
            actual_str = "\n\nACTUAL RESULTS:\n" + immunization.json()
            self.assertEqual(differences, "", expected_str + actual_str)
        else:
            self.assertEqual(differences, "")

    def test_insights_added(self):
        """
        Tests insights found for an immunization.
        """
        input_resource = Immunization.parse_file(
            self.resource_path + "/acd/mock_fhir/input/Immunization.json"
        )
        expected_output = Immunization.parse_file(
            self.resource_path + "/acd/mock_fhir/output/Immunization.json"
        )

        with open(
            self.resource_path + "/acd/mock_acd_output/Immunization.json",
            "r",
            encoding="utf-8",
        ) as f:
            acd_result = ContainerAnnotation.from_dict(json.loads(f.read()))
        self._check_results(input_resource, acd_result, expected_output, True)

    def test_no_insights(self):
        """
        Tests no insights found for an immunization.
        """
        immunization = Immunization.parse_file(
            self.resource_path + "/acd/mock_fhir/input/Immunization_NoInsights.json"
        )
        expected_output = Immunization.parse_file(
            self.resource_path + "/acd/mock_fhir/input/Immunization_NoInsights.json"
        )

        # None shuold be returned from call to add insights
        with open(
            self.resource_path + "/acd/mock_acd_output/Condition_Nothing_Useful.json",
            "r",
            encoding="utf-8",
        ) as f:
            acd_result = ContainerAnnotation.from_dict(json.loads(f.read()))

        ai_results = [
            CodeableConceptAcdInsight(
                adjusted_concept=AdjustedConceptRef(
                    concept_ref=CodeableConceptRef(
                        type=CodeableConceptRefType.VACCINE,
                        code_ref=immunization.vaccineCode,
                        fhir_path="Immunization.vaccineCode",
                    ),
                    adjusted_text=immunization.vaccineCode.text,
                ),
                acd_response=acd_result,
            )
        ]

        num_updates = update_codeable_concepts_and_meta_with_insights(
            immunization, ai_results
        )
        self.assertEqual(0, num_updates, "Did not expect results, but some returned")

        # Verify input_resource was not modified
        differences = DeepDiff(expected_output, immunization, verbose_level=2)
        self.assertEqual(
            differences,
            {},
            "Results do not match expected.\nDIFFERENCES:\n"
            + str(differences)
            + "\nEXPECTED RESULTS:\n"
            + expected_output.json()
            + "\nACTUAL RESULTS:\n"
            + immunization.json(),
        )

    def _immunization_bundle_update(self, input_json, expected_json, acd_result):
        """
        Tests enrich_fhir_resource correctly identifies as Immunization and creates bundle
        """
        immunization = Immunization.parse_file(input_json)

        if expected_json is not None:
            expected_bundle = Bundle.parse_file(expected_json)
        else:
            expected_bundle = None

        ai_results = [
            CodeableConceptAcdInsight(
                adjusted_concept=AdjustedConceptRef(
                    concept_ref=CodeableConceptRef(
                        type=CodeableConceptRefType.VACCINE,
                        code_ref=immunization.vaccineCode,
                        fhir_path="Immunization.vaccineCode",
                    ),
                    adjusted_text=immunization.vaccineCode.text,
                ),
                acd_response=acd_result,
            )
        ]

        result = enrich_resource_codeable_concepts(ai_results, immunization)

        if expected_bundle is None:
            self.assertTrue(result is None, "Expected no allergy created")
        else:
            differences = DeepDiff(expected_bundle, result, verbose_level=2)

            # Differences str should be empty if results match expected
            self.assertEqual(
                differences,
                {},
                "Results do not match expected.\nDIFFERENCES:\n"
                + str(differences)
                + "\nEXPECTED RESULTS:\n"
                + expected_bundle.json()
                + "\nACTUAL RESULTS:\n"
                + result.json(),
            )

    def test_single_resource_update_immunization(self):
        """
        Tests enrich_fhir_resource correctly identifies as Immunization and creates bundle
        """
        input_json = self.resource_path + "/acd/mock_fhir/input/Immunization.json"
        expected_json = (
            self.resource_path + "/acd/mock_fhir/output/Bundle_update_immunization.json"
        )
        with open(
            self.resource_path + "/acd/mock_acd_output/Immunization.json",
            "r",
            encoding="utf-8",
        ) as f:
            acd_result = ContainerAnnotation.from_dict(json.loads(f.read()))
        self._immunization_bundle_update(input_json, expected_json, acd_result)


if __name__ == "__main__":
    unittest.main()
