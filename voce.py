import tempfile

import edge_tts
import gradio as gr
from transformers import pipeline

language_dict = {
  "Italian": {
    "Isabella": "it-IT-IsabellaNeural",
    "Diego": "it-IT-DiegoNeural",
    "Elsa": "it-IT-ElsaNeural"
  }
}

async def text_to_speech_edge(text, language_code, speaker):

    # Get the voice for the selected language and speaker
    voice = language_dict[language_code][speaker]
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
      tmp_path = tmp_file.name
      await communicate.save(tmp_path)

    return text, tmp_path


def get_speakers(language):
    print(language)
    speakers = list(language_dict[language].keys())
    return gr.Dropdown(choices=speakers, value=speakers[0], interactive=True)

default_language = "Italian"
default_speaker = "Isabella"
with gr.Blocks(title="Italian TTS") as demo:
    gr.HTML("<center><h1>Italian TTS (Edge TTS)</h1></center>")
    gr.Markdown("**Nota:** Questo strumento supporta solo la lingua italiana.")
    with gr.Row():
        with gr.Column():
            input_text = gr.Textbox(lines=5, label="Testo in ingresso", placeholder="Inserisci il testo da convertire in voce")
            language = gr.Dropdown(
                choices=list(language_dict.keys()), value=default_language, label="Lingua", interactive=False
            )
            speaker = gr.Dropdown(choices=[], value=default_speaker, label="Speaker", interactive=True)
            run_btn = gr.Button(value="Genera Audio", variant="primary")

        with gr.Column():
            output_text = gr.Textbox(label="Testo in uscita")
            output_audio = gr.Audio(type="filepath", label="Audio Output")

    language.change(get_speakers, inputs=[language], outputs=[speaker])
    run_btn.click(text_to_speech_edge, inputs=[input_text, language, speaker], outputs=[output_text, output_audio])

if __name__ == "__main__":
    demo.queue().launch(share=False)
