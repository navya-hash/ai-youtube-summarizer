# Import necessary libraries for the YouTube bot
import os

import gradio as gr
import re  #For extracting video id 
from youtube_transcript_api import YouTubeTranscriptApi  # For extracting transcripts from YouTube videos
from langchain.text_splitter import RecursiveCharacterTextSplitter  # For splitting text into manageable segments
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS  # For efficient vector storage and similarity search
from langchain.chains import LLMChain  # For creating chains of operations with LLMs
from langchain.prompts import PromptTemplate  # For defining prompt templates
import os
from dotenv import load_dotenv

load_dotenv()


SUPPORTED_LANGUAGES = [
    "English",
    "Hindi",
    "Spanish",
    "French",
    "German",
    "Japanese",
    "Gujarati",
]

LANGUAGE_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Gujarati": "gu",
}



"""
Typical form of you tube video-->https://www.youtube.com/watch?v=VIDEO_ID
 https://www.youtube.com/watch?v=dBGUmUQhjaM&list=PLgUwDviBIf0pcIDCZnxhv0LkHf5KzG9zp
The VIDEO_ID is a unique 11-character string that identifies the video. 
To extract this ID, we'll use a regular expression that captures this 11-character string from the URL.

"""

def get_video_id(url):    
    # Regex pattern to match YouTube video URLs
    pattern = r'https:\/\/www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None




"""
The YouTubeTranscriptApi allows us to retrieve transcripts (subtitles) for a given video. This function first extracts the video ID from the YouTube URL, then fetches the transcripts available for that video. Transcripts 
can be either automatically generated or manually provided by the video uploader.
"""


def _pick_transcript(transcripts, language_code):
    """Pick the best transcript for a language (manual preferred over auto-generated)."""
    generated_match = None
    for t in transcripts:
        code = t.language_code.split("-")[0]
        if code != language_code:
            continue
        if not t.is_generated:
            return t.fetch()
        if generated_match is None:
            generated_match = t.fetch()
    return generated_match


def get_transcript(url, language="English"):
    video_id = get_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL.")

    ytt_api = YouTubeTranscriptApi()
    transcripts = ytt_api.list(video_id)

    requested_code = LANGUAGE_CODES.get(language, "en")
    transcript = _pick_transcript(transcripts, requested_code)

    # Fall back to English, then any available transcript for translation in prompts
    if transcript is None and requested_code != "en":
        transcript = _pick_transcript(transcripts, "en")
    if transcript is None:
        for t in transcripts:
            transcript = t.fetch()
            break

    return transcript if transcript else None




"""
{
    "text": "Transcript text here",
    "start": 0.0,
    "duration": 3.0
}
text: The spoken text from the video.

start: The time (in seconds) when the text starts in the video.

duration: The duration (in seconds) for which the text is displayed.
"""

def process(transcript):
    # Initialize an empty string to hold the formatted transcript
    txt = ""
    
    # Loop through each entry in the transcript
    for i in transcript:
        try:
            # Append the text and its start time to the output string
            txt += f"Text: {i.text} Start: {i.start}\n"
        except KeyError:
            # If there is an issue accessing 'text' or 'start', skip this entry
            pass
            
    # Return the processed transcript as a single string
    return txt


def chunk_transcript(processed_transcript, chunk_size=200, chunk_overlap=20):
    # Initialize the RecursiveCharacterTextSplitter with specified chunk size and overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    # Split the transcript into chunks
    chunks = text_splitter.split_text(processed_transcript)
    return chunks





def get_google_api_key():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Get an API key from https://aistudio.google.com/apikey"
        )
    return api_key


def initialize_gemini_llm():
    return GoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=get_google_api_key(),
        temperature=0,
        max_output_tokens=900,
    )


def setup_embedding_model():
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=get_google_api_key(),
    )



"""
Implementing FAISS for similarity search
FAISS (Facebook AI Similarity Search) is a library designed for efficient similarity 
search and clustering of dense vectors, enabling rapid retrieval of nearest neighbors 
in high-dimensional spaces. This function creates a FAISS index from a list of text chunks
 using the specified embedding model. By converting text chunks into embeddings and indexing
   them with FAISS, we can quickly find the most similar chunks based on cosine similarity 
   or other distance metrics. This is particularly useful in applications such as information retrieval, 
   recommendation systems, and natural language understanding.
"""

def create_faiss_index(chunks, embedding_model):
    """
    Create a FAISS index from text chunks using the specified embedding model.
    
    :param chunks: List of text chunks
    :param embedding_model: The embedding model to use
    <span data-type="emoji" data-name="return"></span> FAISS index
    """
    # Use the FAISS library to create an index from the provided text chunks
    return FAISS.from_texts(chunks, embedding_model)



def create_summary_prompt():
    """
    Create a PromptTemplate for summarizing a YouTube video transcript.
    
    <span data-type="emoji" data-name="return"></span> PromptTemplate object
    """
    template = """
    You are an AI assistant tasked with summarizing YouTube video transcripts. Provide concise, informative summaries that capture the main points of the video content.

    Instructions:
    1. Summarize the transcript in a single concise paragraph in {language}.
    2. Ignore any timestamps in your summary.
    3. Focus on the spoken content (Text) of the video.
    4. If the transcript is in a different language, translate it while summarizing.

    Note: In the transcript, "Text" refers to the spoken words in the video, and "start" indicates the timestamp when that part begins in the video.

    Summarize this transcript in {language}:

    {transcript}
    """

    return PromptTemplate(
        input_variables=["transcript", "language"],
        template=template,
    )


def create_summary_chain(llm, prompt, verbose=True):
    """
    Create an LLMChain for generating summaries.
    
    :param llm: Language model instance
    :param prompt: PromptTemplate instance
    :param verbose: Boolean to enable verbose output (default: True)
    <span data-type="emoji" data-name="return"></span> LLMChain instance
    """
    return LLMChain(llm=llm, prompt=prompt, verbose=verbose)


def create_sentiment_chain(llm, prompt, verbose=True):
    """Create an LLMChain for sentiment analysis."""
    return LLMChain(llm=llm, prompt=prompt, verbose=verbose)


def _chain_result(result):
    return result.get("text", result) if isinstance(result, dict) else result


def _fetch_and_process(video_url, language="English"):
    if not video_url:
        return None, "Please provide a valid YouTube URL."

    try:
        raw_transcript = get_transcript(video_url, language)
        processed = process(raw_transcript)
    except Exception as e:
        return None, f"Error fetching transcript: {e}"

    if not processed.strip():
        return None, "No transcript available for this video."

    return processed, None


def retrieve(query, faiss_index, k=7):
    """
    Retrieve relevant context from the FAISS index based on the user's query.

    Parameters:
        query (str): The user's query string.
        faiss_index (FAISS): The FAISS index containing the embedded documents.
        k (int, optional): The number of most relevant documents to retrieve (default is 3).

    Returns:
        list: A list of the k most relevant documents (or document chunks).
    """
    relevant_context = faiss_index.similarity_search(query, k=k)
    return relevant_context




def create_qa_prompt_template():
    """
    Create a PromptTemplate for question answering based on video content.

    Returns:
        PromptTemplate: A PromptTemplate object configured for Q&A tasks.
    """
    qa_template = """
    You are an expert assistant providing detailed answers based on the following video content.

    Relevant Video Context: {context}

    Based on the above context, please answer the following question in {language}.
    If the context is in a different language, translate your answer appropriately.

    Question: {question}
    """

    return PromptTemplate(
        input_variables=["context", "question", "language"],
        template=qa_template,
    )


def create_sentiment_prompt():
    """Create a PromptTemplate for sentiment analysis on a video transcript."""
    template = """
    Analyze the sentiment of the following YouTube video transcript.

    Provide your analysis in this exact format:
    Overall sentiment: [Positive / Negative / Neutral / Mixed / Informative]
    Confidence: [Low / Medium / High]
    Key emotions:
    - [emotion 1]
    - [emotion 2]
    - [emotion 3]

    Explanation:
    [2-4 sentences explaining the sentiment based on the transcript content. Use {language} for the explanation.]

    Transcript:
    {transcript}
    """

    return PromptTemplate(
        input_variables=["transcript", "language"],
        template=template,
    )


"""
# Creating the Q&A prompt template 
qa_prompt_template = create_qa_prompt_template()

# Example of how to use the prompt template with context and a question
context = "This video explains the fundamentals of quantum physics."
question = "What are the key principles discussed in the video?"

# Generating the prompt
generated_prompt = qa_prompt_template.format(context=context, question=question)

# Output the generated prompt
print(generated_prompt)



output:
You are an expert assistant providing detailed answers based on the following video content.

Relevant Video Context: This video explains the fundamentals of quantum physics.

Based on the above context, please answer the following question:
Question: What are the key principles discussed in the video?
"""


def create_qa_chain(llm, prompt_template, verbose=True):
    """
    Create an LLMChain for question answering.

    Args:
        llm: Language model instance
            The language model to use in the chain (e.g., Google Gemini).
        prompt_template: PromptTemplate
            The prompt template to use for structuring inputs to the language model.
        verbose: bool, optional (default=True)
            Whether to enable verbose output for the chain.

    Returns:
        LLMChain: An instantiated LLMChain ready for question answering.
    """
    
    return LLMChain(llm=llm, prompt=prompt_template, verbose=verbose)



def generate_answer(question, faiss_index, qa_chain, language, k=7):
    """
    Retrieve relevant context and generate an answer based on user input.

    Args:
        question: str
            The user's question.
        faiss_index: FAISS
            The FAISS index containing the embedded documents.
        qa_chain: LLMChain
            The question-answering chain (LLMChain) to use for generating answers.
        language: str
            The language in which the answer should be returned.
        k: int, optional (default=3)
            The number of relevant documents to retrieve.

    Returns:
        str: The generated answer to the user's question.
    """

    relevant_context = retrieve(question, faiss_index, k=k)
    context = "\n\n".join(doc.page_content for doc in relevant_context)
    return qa_chain.predict(context=context, question=question, language=language)


def summarize_video(video_url, language="English"):
    processed_transcript, error = _fetch_and_process(video_url, language)
    if error:
        return error

    llm = initialize_gemini_llm()
    summary_chain = create_summary_chain(llm, create_summary_prompt())
    result = summary_chain.invoke({
        "transcript": processed_transcript,
        "language": language,
    })
    return _chain_result(result)


def analyze_sentiment(video_url, language="English"):
    processed_transcript, error = _fetch_and_process(video_url, language)
    if error:
        return error

    llm = initialize_gemini_llm()
    sentiment_chain = create_sentiment_chain(llm, create_sentiment_prompt())
    result = sentiment_chain.invoke({
        "transcript": processed_transcript,
        "language": language,
    })
    return _chain_result(result)


def answer_question(video_url, user_question, language="English"):
    """
    Title: Answer User's Question

    Description:
    This function retrieves relevant context from the FAISS index based on the user’s query 
    and generates an answer using the preprocessed transcript.

    Args:
        video_url (str): The URL of the YouTube video from which the transcript is to be fetched.
        user_question (str): The question posed by the user regarding the video.
        language (str): The language in which the answer should be returned.

    Returns:
        str: The answer to the user's question or a message indicating that the transcript 
             has not been fetched.
    """
    if not user_question:
        return "Please provide a valid question."

    processed_transcript, error = _fetch_and_process(video_url, language)
    if error:
        return error

    chunks = chunk_transcript(processed_transcript)
    llm = initialize_gemini_llm()
    embedding_model = setup_embedding_model()
    faiss_index = create_faiss_index(chunks, embedding_model)
    qa_chain = create_qa_chain(llm, create_qa_prompt_template())
    return generate_answer(user_question, faiss_index, qa_chain, language)



"""
 Gradio interface for interacting with a YouTube video, allowing users to fetch its transcript, summarize it, or ask questions based on the content of the video. The interface is built using Gradio's Blocks API, which facilitates the creation of interactive web applications with minimal code.
"""


with gr.Blocks() as interface:
    video_url = gr.Textbox(label="YouTube Video URL", placeholder="Enter the YouTube Video URL")
    language_dropdown = gr.Dropdown(
        choices=SUPPORTED_LANGUAGES,
        value="English",
        label="Output Language",
    )

    summary_output = gr.Textbox(label="Video Summary", lines=5)
    question_input = gr.Textbox(label="Ask a Question About the Video", placeholder="Ask your question")
    answer_output = gr.Textbox(label="Answer to Your Question", lines=5)
    sentiment_output = gr.Textbox(label="Sentiment Analysis", lines=8)

    summarize_btn = gr.Button("Summarize Video")
    question_btn = gr.Button("Ask a Question")
    sentiment_btn = gr.Button("Analyze Sentiment")

    summarize_btn.click(
        summarize_video,
        inputs=[video_url, language_dropdown],
        outputs=summary_output,
    )
    question_btn.click(
        answer_question,
        inputs=[video_url, question_input, language_dropdown],
        outputs=answer_output,
    )
    sentiment_btn.click(
        analyze_sentiment,
        inputs=[video_url, language_dropdown],
        outputs=sentiment_output,
    )

# Launch the app with specified server name and port
interface.launch()



