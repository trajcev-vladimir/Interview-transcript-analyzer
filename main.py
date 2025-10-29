import re
import gradio as gr
import json
import log_utils
from pipeline import EvalPipeline
import report_output
from datetime import datetime
import os
import logging

logger = logging.getLogger("main")

def process_transcript(transcript_text, candidate_name, interviewer_name):
    try:
        # Validate Inputs
        if candidate_name.strip() == "":
            return "Please enter Candidate Name", None, None
        if interviewer_name.strip() == "":
            return "Please enter Interviewer Name", None, None
        if not transcript_text or not transcript_text.strip():
            return "Please upload a file or paste transcript text", None, None

        text = transcript_text.strip()

        # Validate presence of names inside transcript
        matches_can = re.findall(rf'\b{re.escape(candidate_name)}\b', text)
        matches_int = re.findall(rf'\b{re.escape(interviewer_name)}\b', text)

        if len(matches_can) == 0:
            return "Candidate name does not match transcript content", None, None
        if len(matches_int) == 0:
            return "Interviewer name does not match transcript content", None, None

        log = f"Evaluation started for Candidate: {candidate_name}"
        logger.info(log), log_utils.log(log)

        # ---- Run Pipeline ----
        try:
            pipeline = EvalPipeline(text, candidate_name, interviewer_name)
            report = pipeline.evaluate_transcript()

        except Exception as e:
            logger.exception("Pipeline execution failed")
            log_utils.log(f"Pipeline Error: {e}")
            return f"Evaluation Failed: {str(e)}", None, None

        log = "Successful Evaluation for all criteria"
        logger.info(log), log_utils.log(log)

        # ---- Export Reports ----
        try:
            export_eng = report_output.Export(report, candidate_name)
            report_url = export_eng.json_report()
            full_report_url = export_eng.full_report()
            log = "Reports successfully exported"
            logger.info(log), log_utils.log(log)
        except Exception as e:
            logger.exception("Report export failed")
            log_utils.log(f"Report Export Error: {e}")
            return f"Evaluation succeeded but report export failed: {e}", None, None

        # ---- Save Logs ----
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_utils.save_logs_to_file(f"./logs/{candidate_name}_req_ID_{timestamp}.log")
        except Exception as e:
            logger.error(f"Failed saving logs: {e}")

        return json.dumps(report, indent=2), report_url, full_report_url

    except Exception as e:
        # Catch any unexpected crash
        logger.exception("Unexpected error in process_transcript")
        log_utils.log(f"Unexpected Error: {e}")
        return f"Critical Error: {str(e)}", None, None

# Wrapper to handle file or text input
def handle_input(file_input, transcript_text, candidate_name, interviewer_name):
    if file_input is not None:
        try:
            # Gradio returns a path string for file_input
            if isinstance(file_input, str) and os.path.exists(file_input):
                with open(file_input, "r", encoding="utf-8") as f:
                    transcript_text = f.read()
            else:
                return "Invalid file input", None, None
        except Exception as e:
            return f"Error reading file: {e}", None, None

    return process_transcript(transcript_text, candidate_name, interviewer_name)

# Gradio UI
with gr.Blocks(title="Candidate Evaluation Report Generator") as demo:
    gr.Markdown("## 🧾 Candidate Evaluation Report Generator")
    gr.Markdown("Upload a transcript or paste text, enter Candidate ID, and generate structured evaluation JSON.")

    with gr.Row():
        file_input = gr.File(label="Upload Transcript (.txt)", file_types=["text"])
        candidate_name = gr.Textbox(label="Candidate Name", placeholder="e.g. Jon Smith")
        interviewer_name = gr.Textbox(label="Interviewer Name", placeholder="e.g. Marta Hulk")

    transcript_text = gr.Textbox(label="Or Paste Transcript Text", lines=8, placeholder="Paste transcript text here...")

    generate_btn = gr.Button("Generate JSON Report")

    json_output = gr.Code(label="Generated JSON", language="json")
    download_btn_rep = gr.File(label="Download JSON Report")
    download_btn_full_rep = gr.File(label="Download Full Report")

    generate_btn.click(
        handle_input,
        inputs=[file_input, transcript_text, candidate_name, interviewer_name],
        outputs=[json_output, download_btn_rep, download_btn_full_rep]
    )

demo.launch()