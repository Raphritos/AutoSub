import os
import sys
import subprocess
import threading
import time
import gc
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import whisper
import srt
from datetime import timedelta
from googletrans import Translator

# --- INJEÇÃO DO FFMPEG NA VENV / RUNTIME ---
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

# --- CORREÇÃO PARA PYINSTALLER E STDOUT ---
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

def resource_path(relative_path):
    """ Retorna o caminho absoluto do recurso (funciona em dev e para PyInstaller) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    whisper_assets = os.path.join(base_path, 'whisper', 'assets')
    if os.path.exists(whisper_assets):
        os.environ['WHISPER_ASSETS'] = whisper_assets
    os.environ["PATH"] += os.pathsep + base_path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class AutoSubApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AutoSub - Automatic Subtitle Generator (v0.5.1)")
        self.geometry("840x880")
        self.resizable(False, False)

        # --- ÍCONE DA JANELA ---
        icon_file = resource_path("autosub.ico")
        if os.path.exists(icon_file):
            try:
                self.iconbitmap(icon_file)
            except Exception:
                pass

        self.caminho_arquivo = ""
        self.pasta_destino_custom = ""
        self.cancelar = False
        self.ultimo_srt = ""
        self.modelo_whisper = None
        self.idioma_interface = "en"  # Padrão em Inglês

        self.textos = {
            "en": {
                "titulo": "AutoSub",
                "subtitulo": "Automatic Subtitle Generator (100% Free)",
                "btn_selecionar": "📂 Select Video/Audio",
                "lbl_arquivo": "No file selected",
                "lbl_destino": "📂 Output Folder (Optional):",
                "lbl_destino_padrao": "Default (Same as source file)",
                "btn_browse_destino": "Browse...",
                "lbl_idioma": "🌐 Audio Language:",
                "lbl_modelo": "🧠 Whisper Model:",
                "lbl_formato": "📄 Output Format:",
                "chk_traduzir": "Translate to Portuguese (BR)",
                "btn_gerar": "▶ Generate Subtitles",
                "btn_cancelar": "⏹ Cancel",
                "btn_abrir_pasta": "📂 Open Output Folder",
                "status_aguardando": "Waiting...",
                "status_carregar_modelo": "Loading model...",
                "status_transcrever": "Transcribing audio...",
                "status_traduzir": "Translating...",
                "status_gerar": "Generating subtitles...",
                "status_concluido": "Completed!",
                "msg_sucesso": "Subtitles generated successfully!\n\nSaved at:\n",
                "msg_erro": "An error occurred:\n",
                "msg_aviso_arquivo": "Please select a file first!",
                "msg_cancelado": "Cancel request received. Stopping...",
                "log_inicial": "[INFO] AutoSub v0.5.1 ready. Select a file...",
                "log_arquivo": "[INFO] File loaded: ",
                "log_destino": "[INFO] Output directory set to: ",
                "log_modelo_carregando": "[INFO] Loading Whisper model: ",
                "log_modelo_carregado": "[INFO] Model loaded!",
                "log_transcrevendo": "[INFO] Transcribing audio... (this may take a while)",
                "log_transcricao_concluida": "[INFO] Transcription completed! {} segments found.",
                "log_traduzindo": "[INFO] Translating to Portuguese (BR)...",
                "log_traducao_concluida": "[INFO] Translation completed! Success: {}, Failures: {}",
                "log_gerando": "[INFO] Generating subtitle file...",
                "log_sucesso": "[SUCCESS] Subtitles generated at: ",
                "log_erro": "[ERROR] An error occurred: ",
                "log_cancelado": "[CANCELLED] Process interrupted.",
                "log_aviso_traducao": "[WARNING] Failed to translate segment {}: {}"
            },
            "pt": {
                "titulo": "AutoSub",
                "subtitulo": "Gerador de Legendas Automáticas (100% Grátis)",
                "btn_selecionar": "📂 Selecionar Vídeo/Áudio",
                "lbl_arquivo": "Nenhum arquivo selecionado",
                "lbl_destino": "📂 Pasta de Destino (Opcional):",
                "lbl_destino_padrao": "Padrão (Mesma pasta do arquivo)",
                "btn_browse_destino": "Buscar...",
                "lbl_idioma": "🌐 Idioma do Áudio:",
                "lbl_modelo": "🧠 Modelo Whisper:",
                "lbl_formato": "📄 Formato de Saída:",
                "chk_traduzir": "Traduzir para Português (BR)",
                "btn_gerar": "▶ Gerar Legendas",
                "btn_cancelar": "⏹ Cancelar",
                "btn_abrir_pasta": "📂 Abrir Pasta de Destino",
                "status_aguardando": "Aguardando...",
                "status_carregar_modelo": "Carregando modelo...",
                "status_transcrever": "Transcrevendo áudio...",
                "status_traduzir": "Traduzindo...",
                "status_gerar": "Gerando legendas...",
                "status_concluido": "Concluído!",
                "msg_sucesso": "Legendas geradas com sucesso!\n\nSalvo em:\n",
                "msg_erro": "Ocorreu um erro:\n",
                "msg_aviso_arquivo": "Selecione um arquivo primeiro!",
                "msg_cancelado": "Pedido de cancelamento recebido. Parando...",
                "log_inicial": "[INFO] AutoSub v0.5.1 pronto. Selecione um arquivo...",
                "log_arquivo": "[INFO] Arquivo carregado: ",
                "log_destino": "[INFO] Diretório de saída definido para: ",
                "log_modelo_carregando": "[INFO] Carregando modelo Whisper: ",
                "log_modelo_carregado": "[INFO] Modelo carregado!",
                "log_transcrevendo": "[INFO] Transcrevendo áudio... (pode demorar um pouco)",
                "log_transcricao_concluida": "[INFO] Transcrição concluída! {} segmentos encontrados.",
                "log_traduzindo": "[INFO] Traduzindo para Português (BR)...",
                "log_traducao_concluida": "[INFO] Tradução concluída! Sucesso: {}, Falhas: {}",
                "log_gerando": "[INFO] Gerando arquivo de legendas...",
                "log_sucesso": "[SUCESSO] Legendas geradas em: ",
                "log_erro": "[ERRO] Ocorreu um erro: ",
                "log_cancelado": "[CANCELADO] Processo interrompido.",
                "log_aviso_traducao": "[AVISO] Falha ao traduzir segmento {}: {}"
            }
        }

        # --- Topo ---
        self.frame_topo = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_topo.pack(fill="x", pady=(15, 5), padx=30)

        self.label_titulo = ctk.CTkLabel(self.frame_topo, text=self.textos[self.idioma_interface]["titulo"], font=ctk.CTkFont(size=26, weight="bold"), text_color="#00ffcc")
        self.label_titulo.pack(side="left", expand=True)

        self.btn_idioma = ctk.CTkButton(self.frame_topo, text="🇧🇷 PT", width=80, command=self.alternar_idioma, fg_color="#444444", hover_color="#555555")
        self.btn_idioma.pack(side="right")

        self.label_sub = ctk.CTkLabel(self, text=self.textos[self.idioma_interface]["subtitulo"], font=ctk.CTkFont(size=12), text_color="#aaaaaa")
        self.label_sub.pack(pady=(0, 15))

        # --- Seleção do Arquivo ---
        self.frame_selecao = ctk.CTkFrame(self, corner_radius=10)
        self.frame_selecao.pack(pady=5, padx=30, fill="x")

        self.btn_selecionar = ctk.CTkButton(self.frame_selecao, text=self.textos[self.idioma_interface]["btn_selecionar"], command=self.selecionar_arquivo, width=200)
        self.btn_selecionar.pack(side="left", padx=15, pady=12)

        self.lbl_arquivo = ctk.CTkLabel(self.frame_selecao, text=self.textos[self.idioma_interface]["lbl_arquivo"], text_color="#aaaaaa")
        self.lbl_arquivo.pack(side="left", padx=10, fill="x", expand=True)

        # --- Seleção do Destino ---
        self.frame_destino = ctk.CTkFrame(self, corner_radius=10)
        self.frame_destino.pack(pady=5, padx=30, fill="x")

        self.lbl_destino_titulo = ctk.CTkLabel(self.frame_destino, text=self.textos[self.idioma_interface]["lbl_destino"])
        self.lbl_destino_titulo.pack(side="left", padx=15, pady=12)

        self.lbl_destino_path = ctk.CTkLabel(self.frame_destino, text=self.textos[self.idioma_interface]["lbl_destino_padrao"], text_color="#aaaaaa")
        self.lbl_destino_path.pack(side="left", padx=10, fill="x", expand=True)

        self.btn_destino = ctk.CTkButton(self.frame_destino, text=self.textos[self.idioma_interface]["btn_browse_destino"], command=self.selecionar_destino, width=100, fg_color="#444444", hover_color="#555555")
        self.btn_destino.pack(side="right", padx=15, pady=12)

        # --- Opções ---
        self.frame_opcoes = ctk.CTkFrame(self, corner_radius=10)
        self.frame_opcoes.pack(pady=10, padx=30, fill="x")

        self.lbl_idioma = ctk.CTkLabel(self.frame_opcoes, text=self.textos[self.idioma_interface]["lbl_idioma"])
        self.lbl_idioma.grid(row=0, column=0, padx=15, pady=8, sticky="w")

        self.idiomas = {
            "Auto-detect": None,
            "English": "en",
            "Portuguese": "pt",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Italian": "it",
            "Japanese": "ja"
        }

        self.combo_idioma = ctk.CTkComboBox(self.frame_opcoes, values=list(self.idiomas.keys()), width=250)
        self.combo_idioma.grid(row=0, column=1, padx=15, pady=8, sticky="w")
        self.combo_idioma.set("Auto-detect")

        self.lbl_modelo = ctk.CTkLabel(self.frame_opcoes, text=self.textos[self.idioma_interface]["lbl_modelo"])
        self.lbl_modelo.grid(row=1, column=0, padx=15, pady=8, sticky="w")

        self.modelos = {
            "Tiny (Fastest)": "tiny",
            "Base (Balanced)": "base",
            "Small (More Accurate)": "small"
        }

        self.combo_modelo = ctk.CTkComboBox(self.frame_opcoes, values=list(self.modelos.keys()), width=250)
        self.combo_modelo.grid(row=1, column=1, padx=15, pady=8, sticky="w")
        self.combo_modelo.set("Base (Balanced)")

        self.lbl_formato = ctk.CTkLabel(self.frame_opcoes, text=self.textos[self.idioma_interface]["lbl_formato"])
        self.lbl_formato.grid(row=2, column=0, padx=15, pady=8, sticky="w")

        self.combo_formato = ctk.CTkComboBox(self.frame_opcoes, values=["SRT (.srt)", "VTT (.vtt)"], width=250)
        self.combo_formato.grid(row=2, column=1, padx=15, pady=8, sticky="w")
        self.combo_formato.set("SRT (.srt)")

        self.var_traduzir = tk.BooleanVar()
        self.chk_traduzir = ctk.CTkCheckBox(self.frame_opcoes, text=self.textos[self.idioma_interface]["chk_traduzir"], variable=self.var_traduzir)
        self.chk_traduzir.grid(row=3, column=0, columnspan=2, padx=15, pady=8, sticky="w")

        # --- Ações ---
        self.frame_acoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_acoes.pack(pady=15)

        self.btn_gerar = ctk.CTkButton(self.frame_acoes, text=self.textos[self.idioma_interface]["btn_gerar"], command=self.iniciar_thread, height=45, width=200, font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_gerar.pack(side="left", padx=10)

        self.btn_cancelar = ctk.CTkButton(self.frame_acoes, text=self.textos[self.idioma_interface]["btn_cancelar"], command=self.cancelar_processo, height=45, width=150, fg_color="#cc3333", hover_color="#ff4444", state="disabled", font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_cancelar.pack(side="left", padx=10)

        # --- Status e Progresso ---
        self.progresso = ctk.CTkProgressBar(self, width=780)
        self.progresso.pack(pady=5)
        self.progresso.set(0)

        self.lbl_status = ctk.CTkLabel(self, text=self.textos[self.idioma_interface]["status_aguardando"], text_color="#00ffcc")
        self.lbl_status.pack(pady=5)

        self.btn_abrir_pasta = ctk.CTkButton(self, text=self.textos[self.idioma_interface]["btn_abrir_pasta"], command=self.abrir_pasta, state="disabled", fg_color="#444444", hover_color="#555555")
        self.btn_abrir_pasta.pack(pady=(0, 10))

        # --- Console Log ---
        self.console = ctk.CTkTextbox(self, width=780, height=180, corner_radius=10)
        self.console.pack(pady=10, padx=30, fill="both", expand=True)
        self.console.insert("end", self.textos[self.idioma_interface]["log_inicial"] + "\n")
        self.console.configure(state="disabled")

    def alternar_idioma(self):
        self.idioma_interface = "pt" if self.idioma_interface == "en" else "en"
        self.btn_idioma.configure(text="🇺🇸 EN" if self.idioma_interface == "pt" else "🇧🇷 PT")

        t = self.textos[self.idioma_interface]
        self.label_titulo.configure(text=t["titulo"])
        self.label_sub.configure(text=t["subtitulo"])
        self.btn_selecionar.configure(text=t["btn_selecionar"])
        if not self.caminho_arquivo:
            self.lbl_arquivo.configure(text=t["lbl_arquivo"])
        self.lbl_destino_titulo.configure(text=t["lbl_destino"])
        if not self.pasta_destino_custom:
            self.lbl_destino_path.configure(text=t["lbl_destino_padrao"])
        self.btn_destino.configure(text=t["btn_browse_destino"])
        self.lbl_idioma.configure(text=t["lbl_idioma"])
        self.lbl_modelo.configure(text=t["lbl_modelo"])
        self.lbl_formato.configure(text=t["lbl_formato"])
        self.chk_traduzir.configure(text=t["chk_traduzir"])
        self.btn_gerar.configure(text=t["btn_gerar"])
        self.btn_cancelar.configure(text=t["btn_cancelar"])
        self.btn_abrir_pasta.configure(text=t["btn_abrir_pasta"])
        self.lbl_status.configure(text=t["status_aguardando"])

    def log(self, mensagem):
        self.console.configure(state="normal")
        self.console.insert("end", mensagem + "\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def abrir_pasta(self):
        if self.ultimo_srt and os.path.exists(os.path.dirname(self.ultimo_srt)):
            pasta = os.path.dirname(self.ultimo_srt)
            if sys.platform == "win32":
                os.startfile(pasta)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", pasta])
            else:
                subprocess.Popen(["xdg-open", pasta])

    def selecionar_arquivo(self):
        ficheiro = filedialog.askopenfilename(
            title="Select Video or Audio",
            filetypes=[
                ("All Files", "*.*"),
                ("Videos", "*.mp4 *.mkv *.avi *.mov *.wmv"),
                ("Audios", "*.mp3 *.wav *.m4a *.flac *.ogg")
            ]
        )
        if ficheiro:
            self.caminho_arquivo = os.path.abspath(ficheiro)
            self.lbl_arquivo.configure(text=os.path.basename(ficheiro))
            self.log(self.textos[self.idioma_interface]["log_arquivo"] + os.path.basename(ficheiro))

    def selecionar_destino(self):
        pasta = filedialog.askdirectory(title="Select Output Folder")
        if pasta:
            self.pasta_destino_custom = os.path.abspath(pasta)
            self.lbl_destino_path.configure(text=self.pasta_destino_custom)
            self.log(self.textos[self.idioma_interface]["log_destino"] + self.pasta_destino_custom)

    def cancelar_processo(self):
        self.cancelar = True
        self.log(self.textos[self.idioma_interface]["msg_cancelado"])
        self.btn_cancelar.configure(state="disabled")

    def iniciar_thread(self):
        if not self.caminho_arquivo:
            messagebox.showwarning("Warning", self.textos[self.idioma_interface]["msg_aviso_arquivo"])
            return
        self.btn_selecionar.configure(state="disabled")
        self.btn_destino.configure(state="disabled")
        self.combo_idioma.configure(state="disabled")
        self.combo_modelo.configure(state="disabled")
        self.combo_formato.configure(state="disabled")
        self.chk_traduzir.configure(state="disabled")
        self.btn_gerar.configure(state="disabled")
        self.btn_cancelar.configure(state="normal")
        self.btn_abrir_pasta.configure(state="disabled")
        self.cancelar = False
        threading.Thread(target=self.processar, daemon=True).start()

    def processar(self):
        t = self.textos[self.idioma_interface]
        try:
            modelo_nome = self.modelos.get(self.combo_modelo.get(), "base")
            self.log(t["log_modelo_carregando"] + modelo_nome)
            self.lbl_status.configure(text=t["status_carregar_modelo"])
            self.progresso.set(0.1)

            self.modelo_whisper = whisper.load_model(modelo_nome)
            self.log(t["log_modelo_carregado"])

            if self.cancelar:
                return

            self.log(t["log_transcrevendo"])
            self.lbl_status.configure(text=t["status_transcrever"])
            self.progresso.set(0.3)

            idioma_selecionado = self.idiomas.get(self.combo_idioma.get())
            kwargs = {"verbose": False}
            if idioma_selecionado:
                kwargs["language"] = idioma_selecionado

            resultado = self.modelo_whisper.transcribe(self.caminho_arquivo, **kwargs)

            if not resultado or "segments" not in resultado:
                raise Exception("Failed to extract audio segments.")

            self.progresso.set(0.7)
            self.log(t["log_transcricao_concluida"].format(len(resultado['segments'])))

            if self.cancelar:
                return

            if self.var_traduzir.get():
                self.log(t["log_traduzindo"])
                self.lbl_status.configure(text=t["status_traduzir"])
                tradutor = Translator()
                sucesso, falhas = 0, 0

                for i, seg in enumerate(resultado["segments"]):
                    if self.cancelar:
                        break
                    try:
                        res = tradutor.translate(seg["text"], src='auto', dest='pt')
                        if res and res.text:
                            seg["text"] = res.text
                            sucesso += 1
                        else:
                            falhas += 1
                    except Exception as e:
                        falhas += 1
                        self.log(t["log_aviso_traducao"].format(i+1, e))

                self.progresso.set(0.9)
                self.log(t["log_traducao_concluida"].format(sucesso, falhas))

            self.log(t["log_gerando"])
            self.lbl_status.configure(text=t["status_gerar"])

            legendas = []
            for i, seg in enumerate(resultado["segments"]):
                legendas.append(srt.Subtitle(
                    index=i + 1,
                    start=timedelta(seconds=seg["start"]),
                    end=timedelta(seconds=seg["end"]),
                    content=seg["text"].strip()
                ))

            # Pasta de saída
            if self.pasta_destino_custom and os.path.exists(self.pasta_destino_custom):
                pasta_saida = self.pasta_destino_custom
            else:
                pasta_saida = os.path.dirname(self.caminho_arquivo)

            nome_base = os.path.splitext(os.path.basename(self.caminho_arquivo))[0]
            formato = self.combo_formato.get()
            extensao = ".vtt" if "VTT" in formato else ".srt"

            # Determina a tag do idioma para o nome do arquivo
            if self.var_traduzir.get():
                tag_idioma = "pt-br"
            elif idioma_selecionado:
                tag_idioma = idioma_selecionado
            else:
                tag_idioma = resultado.get("language", "auto")

            # Construção do nome do arquivo único para evitar sobrescrever
            caminho_srt = os.path.join(pasta_saida, f"{nome_base}_{tag_idioma}{extensao}")
            contador = 1
            while os.path.exists(caminho_srt):
                caminho_srt = os.path.join(pasta_saida, f"{nome_base}_{tag_idioma} ({contador}){extensao}")
                contador += 1

            if "VTT" in formato:
                conteudo = srt.compose(legendas, reindex=True, start_index=1)
                with open(caminho_srt, "w", encoding="utf-8") as f:
                    f.write("WEBVTT\n\n" + conteudo.replace(",", "."))
            else:
                with open(caminho_srt, "w", encoding="utf-8") as f:
                    f.write(srt.compose(legendas))

            self.ultimo_srt = caminho_srt
            self.progresso.set(1.0)
            self.lbl_status.configure(text=t["status_concluido"])
            self.log(f"\n{t['log_sucesso']}{caminho_srt}")
            messagebox.showinfo("Success", f"{t['msg_sucesso']}{caminho_srt}")

        except Exception as e:
            self.log(f"{t['log_erro']}{e}")
            messagebox.showerror("Error", f"{t['msg_erro']}{e}")
        finally:
            self.modelo_whisper = None
            gc.collect()

            self.btn_selecionar.configure(state="normal")
            self.btn_destino.configure(state="normal")
            self.combo_idioma.configure(state="normal")
            self.combo_modelo.configure(state="normal")
            self.combo_formato.configure(state="normal")
            self.chk_traduzir.configure(state="normal")
            self.btn_gerar.configure(state="normal")
            self.btn_cancelar.configure(state="disabled")
            self.btn_abrir_pasta.configure(state="normal")

def main():
    app = AutoSubApp()
    app.mainloop()

if __name__ == "__main__":
    main()
