from transformers import pipeline

# Load smaller summarization model
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def generate_explanation(text):

    if len(text) < 50:
        return "Please provide more academic content for explanation."

    summary = summarizer(
        text,
        max_length=80,
        min_length=20,
        do_sample=False
    )

    return summary[0]["summary_text"]