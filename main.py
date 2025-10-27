from pipeline import EvalPipeline
import gradio as gr
import json
import os
import log_utils
from pipeline import EvalPipeline
import report_output
from datetime import datetime


def process_transcript(transcript_text, candidate_id):
    """
    Process uploaded file or text, and generate a structured JSON report.
    """
    # Read transcript either from upload or textbox
    if candidate_id == "":
        json_data = "Please enter Candidate Name"
        return json_data, None, None
    if transcript_text.strip():
        text = transcript_text.strip()
    else:
        json_data = "Please enter Transcript text"
        return json_data, None, None
    print(f"Candidate name: {candidate_id}")


    # Example: generate report based on transcript (stub)
    pipeline = EvalPipeline(text)
    report = pipeline.evaluate_transcript(candidate_id)


    export_eng = report_output.Export(report, candidate_id)
    report_url = export_eng.json_report()
    full_report_url = export_eng.full_report()

    print(f"Full report {full_report_url}")
    print(f"JSON report {report_url}")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_utils.save_logs_to_file(f"./logs/{candidate_id}_req_ID_{timestamp}.log")

    json_data = json.dumps(report, indent=2)

    return json_data, report_url, full_report_url


with gr.Blocks(title="Candidate Evaluation Report Generator") as demo:
    gr.Markdown("## 🧾 Candidate Evaluation Report Generator")
    gr.Markdown("Upload a transcript or paste text, enter Candidate ID, and generate structured evaluation JSON.")

    with gr.Row():
       # file_input = gr.File(label="Upload Transcript (.txt)", file_types=["text"])
        candidate_name = gr.Textbox(label="Candidate ID", placeholder="e.g. CAND123")
        interviewer_name = gr.Textbox(label="Interviewer", placeholder="e.g. ")

    transcript_text = gr.Textbox(label="Or Paste Transcript Text", lines=8, placeholder="Paste transcript text here...")

    generate_btn = gr.Button("Generate JSON Report 🚀")

    json_output = gr.Code(label="Generated JSON", language="json")
    download_btn_rep = gr.File(label="Download JSON Report")
    download_btn_full_rep = gr.File(label="Download Full Report")

    generate_btn.click(
        process_transcript,
        inputs=[transcript_text, candidate_name],
        outputs=[
            json_output,
            download_btn_rep,
            download_btn_full_rep]
    )

demo.launch()
