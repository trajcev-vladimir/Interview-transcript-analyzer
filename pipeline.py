import logging
import json
import yaml
import log_utils
from rag_module import RAGModule
from llm_client import LLMClient, safe_parse_json
from preprocessing import preprocess_transcript


logger = logging.getLogger("EvalPipeline")

class EvalPipeline:
    def __init__(self, transcript_text, config_path="./config/config.yaml"):
    # Open configuration file and fetch values
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.llm = LLMClient(self.config["llm"])
        self.rag = RAGModule(self.config["rag"])
        self.criteria = self.config["pipeline"]["criteria_list"]
        self.confidence_threshold = self.config["pipeline"]["confidence_threshold"]
        self.preproc_text = preprocess_transcript(transcript_text)

        #self.preproc_text =transcript_text
        with open("./config/template.json") as t:
            self.tjson = json.load(t)
    def evaluate_category(self, crit, input_text, candidate_id):
            log= f"Extract category question and description for {crit} criteria"
            logger.info(log), log_utils.log(log)
            category_question = self.tjson[crit]["question"]
            category_description = self.tjson[crit]["description"]

            base_prompt = f"""
            For the candidate: {candidate_id}, evaluate {category_question} {category_description}  based on transcript: {input_text}
                    
                                        Format the output as JSON using the following format excluding json word include proper curly brackets
                                        "confidence": 0-100,
                                        "rationale": "...",
                                        "supporting_excerpts": "...",                     
            """
            print(f"Base promt: {base_prompt}")

            # Response from the LLM
            llm_response = self.llm.run(base_prompt)
            log= f"Successful LLM response for {crit} criteria"
            logger.info(log), log_utils.log(log)

            print(f"Response: {llm_response}") #DELETE at the end

            #Parse the response in JSON to be able to fetch confidence
            parsed_response = safe_parse_json(llm_response)
            print(f"Parsed JSON : {parsed_response}") #DELETE at the end

            # Fetch the confidence, rationale and supporting_excerpts from the response
            confidence = parsed_response.get("confidence")
            print(f"Confidence: {confidence}")
            rationale = parsed_response.get("rationale")
            supporting_excerpts = parsed_response.get("supporting_excerpts")
            log = f"Successful parsed LLM response for {crit} criteria"
            logger.info(log), log_utils.log(log)


            # If low confidence, trigger RAG
            if confidence < self.confidence_threshold * 100:
                log=f"Low confidence ({confidence}) detected for {crit}. -----Invoking RAG-----..."
                logger.warning(log), log_utils.log(log)

                log_utils.print_logs()
                print(f"LOG:{rationale}")
                print(f"LOG:{supporting_excerpts}")

                # Query similar cases from vector database
                rag_cases = self.rag.summarize_similar_cases(input_text)
                if rag_cases == "No similar past cases available.":
                    return {
                        "assessment": rationale,
                        "confidence": confidence,
                        "supporting_excerpts": supporting_excerpts,
                        "review_required": confidence < self.confidence_threshold * 100,
                        "rag_used": "Yes, but no similar past cases available.",
                    }
                print(f"LOG:RAG cases: ({rag_cases}")
                log=f"Similar cases for {crit} returned"
                logger.warning(log), log_utils.log(log)
                summ_prompt = f""" Summarize {rag_cases} in few sentences so they can be used in another prompt for improving confidence 
                """

                # Summarize similar cases to be able to be used in the prompt
                rag_context = self.llm.run(summ_prompt)
                log = f"Successful LLM summarize similar cases for {crit}"
                logger.info(log), log_utils.log(log)
                print(f"RAG summarized context: {rag_context}")

                refinement_prompt = f"""
                Original evaluation (confidence {confidence}%): {rationale}
                For the candidate: {candidate_id} refine and improve the evaluation for {category_question} {category_description} based on Retrieved similar cases for context:
                {rag_context} and transcript: {input_text}
        
                            Format the output as JSON using the following format excluding json word include proper curly brackets:
                            "confidence": 0-100,
                            "rationale": "...",
                            "supporting_excerpts": "...",
                """
                print(f"Refined prompt: {refinement_prompt}")
                refined_llm_response = self.llm.run(refinement_prompt)
                log = f"Successful refined LLM response for {crit}"
                logger.info(log), log_utils.log(log)
                print(f"Refined response : {refined_llm_response}")
                parsed_refined_response = safe_parse_json(refined_llm_response)
                logger.info(f"Refined response for {crit}: {refined_llm_response}")

                refined_confidence= parsed_refined_response.get("confidence")
                refined_rationale = parsed_refined_response.get("rationale")
                refined_supporting_excerpts = parsed_refined_response.get("supporting_excerpts")

                log = f"Confidence after RAG {refined_confidence}"
                logger.info(log), log_utils.log(log)

                print(f"Rezults from rag and LLM")
                return {
                    "LLM assessment": rationale,
                    "LLM confidence": confidence,
                    "LLM supporting_excerpts": supporting_excerpts,
                    "Retrieved similar cases": rag_cases,
                    "Summarized similar cases": rag_context,
                    "assessment": refined_rationale,
                    "RAG confidence": refined_confidence,
                    "RAG supporting_excerpts": refined_supporting_excerpts,
                    "review_required": confidence < self.confidence_threshold * 100,
                    "rag_used": "YES",
                }


            log = f"Successful LLM response for {crit} with confidence {confidence}%"
            logger.info(log), log_utils.log(log)
            return {
                "assessment": rationale,
                "confidence": confidence,
                "supporting_excerpts": supporting_excerpts,
                "review_required": confidence < self.confidence_threshold * 100,
                "rag_used": "NO",
                }
        #
    # def _extract_confidence(self, llm_output: str) -> float:
    #     """
    #     Extract numeric confidence score from LLM response (heuristic).
    #     """
    #     import re
    #     match = re.search(r'(\d{1,3})\s*%', llm_output)
    #     if match:
    #         value = min(100, max(0, int(match.group(1))))
    #         return value
    #     # fallback if no explicit score
    #     return 70.0
    #
    def evaluate_transcript(self, candidate_id):
        """
        Evaluate all categories for one transcript.
        """
        results = {}
        for crit in self.criteria:
            log = f"Evaluating category: ---------------{crit}---------------"
            logger.info(log), log_utils.log(log)
            excerpt = self.preproc_text # use transcript snippet
            results[crit] = self.evaluate_category(crit, excerpt, candidate_id)
        return results

    # def export_json(self):
    #     with open("template.json") as t:
    #         temp_json = json.load(t)
    #
    #     for crit in self.criteria:
    #         # Fetch the question and description for a category from the json template file
    #         temp_json[crit]["question"] = results[crit]["question"]
    #         category_description = tjson[crit]["description"]
